"""
Offline voice commands.

Say "<command> <argument>", e.g. "log, I aligned the cavity", and the matching function is called with the rest of the
sentence ("I aligned the cavity"). Commands with no parameters are called when their phrase is said on its own.

Two speech-to-text engines are supported, chosen by the model folder that is passed to start_voice_listener:
    * Vosk (https://alphacephei.com/vosk/models) - streaming, fast, English.
    * faster-whisper (CTranslate2 Whisper models, e.g. ivrit-ai/whisper-large-v3-turbo-ct2) - transcribes each phrase
      after you stop talking. Slower on CPU, but the only good option for Hebrew.
"""
import difflib
import inspect
import json
import os
import queue
from collections import deque
from pathlib import Path
from typing import Callable

import numpy as np
import sounddevice as sd
from plyer import notification

from local_config import NOTES_PATH
from core.general_gui_controller import paste_value

SAMPLE_RATE = 16000
BLOCK_SIZE = 1600  # 0.1 s of audio per callback
FUZZY_CUTOFF = 0.8  # Minimal difflib ratio for a misheard command word to count (e.g. "blog" -> "log")
PUNCTUATION = ",.!?:;\"'()-–—"
FILLER_WORDS = {"the", "a", "uh", "um", "huh"}  # Skipped before a command and at the end of its argument


def log_notes(note: str, notes_path: str | Path = NOTES_PATH):
    """Append the note as a markdown bullet to the end of the notes file."""
    note = note.strip()
    if not note:
        return
    note = note[0].upper() + note[1:]
    notes_path = Path(notes_path)
    notes_path.parent.mkdir(parents=True, exist_ok=True)

    # Make sure the bullet starts on its own line, even if the file does not end with a newline.
    prefix = ""
    if notes_path.exists() and notes_path.stat().st_size > 0:
        with open(notes_path, "rb") as f:
            f.seek(-1, 2)
            if f.read(1) != b"\n":
                prefix = "\n"

    with open(notes_path, "a", encoding="utf-8") as f:
        f.write(f"{prefix}* Voice log: {note}\n")

    print(f"Logged: {note}")
    _notify("Note logged", note)


def type_text(text: str):
    """Paste the text at the current cursor position."""
    paste_value(value=text, location=None, click=False, delete_existing=False)


# type_text is not a default: a misheard "type" would paste text into whatever window is focused.
# Opt in with command_map={"type": type_text}.
DEFAULT_COMMANDS: dict[str, Callable] = {"log": log_notes, "notebook": log_notes, "note book": log_notes, "רשום": log_notes}


def _notify(title: str, message: str):
    try:
        notification.notify(title=title, message=message, timeout=2)
    except Exception as e:  # Notifications are a nicety - never let them kill the listener
        print(f"[Notification failed]: {e}")


def _takes_argument(func: Callable) -> bool:
    return len(inspect.signature(func).parameters) >= 1


def match_command(text: str, command_map: dict[str, Callable]) -> tuple[str, str] | None:
    """
    Find the command said at the start of the text. Returns (command, argument) or None.
    Command words are compared without case and punctuation ("Log, I did..." matches "log"), first exactly and then
    fuzzily. The argument keeps its original case and punctuation.
    """
    words = [w for w in text.split() if w.strip(PUNCTUATION)]
    normalized = [w.strip(PUNCTUATION).lower() for w in words]

    command = _match_leading_words(normalized, command_map)
    if command is None:  # Vosk often hears breath/noise as "the" - retry without leading filler words
        n_fillers = 0
        while n_fillers < len(normalized) and normalized[n_fillers] in FILLER_WORDS:
            n_fillers += 1
        words, normalized = words[n_fillers:], normalized[n_fillers:]
        command = _match_leading_words(normalized, command_map) if n_fillers else None
    if command is None:
        return None

    argument = words[len(command.split()):]
    while argument and argument[-1].strip(PUNCTUATION).lower() in FILLER_WORDS:
        argument.pop()
    return command, " ".join(argument)


def _match_leading_words(normalized: list[str], command_map: dict[str, Callable]) -> str | None:
    """The command that the first words are (exactly, or else the most similar one above FUZZY_CUTOFF)."""
    # Longest commands first, so "zoom in" is not shadowed by a hypothetical "zoom".
    commands = sorted(command_map, key=lambda c: len(c.split()), reverse=True)
    best_command, best_ratio = None, FUZZY_CUTOFF
    for command in commands:
        n = len(command.split())
        if len(normalized) < n:
            continue
        heard = " ".join(normalized[:n])
        if heard == command:
            return command
        ratio = difflib.SequenceMatcher(None, heard, command).ratio()
        if ratio >= best_ratio:
            best_command, best_ratio = command, ratio
    return best_command


def run_command(text: str, command_map: dict[str, Callable]) -> bool:
    """Run the command said in the text. Returns whether a command was found."""
    match = match_command(text, command_map)
    if match is None:
        return False
    command, argument = match
    func = command_map[command]
    try:
        if _takes_argument(func):
            func(argument)
        elif argument:
            print(f"[Ignored]: '{command}' takes no argument, but heard '{text}'")
        else:
            func()
    except Exception as e:
        print(f"[ERROR running '{command}' with argument '{argument}']: {e}")
    return True


class _VoskEngine:
    def __init__(self, model_path: Path):
        import vosk
        self.recognizer = vosk.KaldiRecognizer(vosk.Model(str(model_path)), SAMPLE_RATE)

    def feed(self, chunk: bytes) -> str | None:
        if self.recognizer.AcceptWaveform(chunk):
            return json.loads(self.recognizer.Result()).get("text", "")
        return None


class _WhisperEngine:
    """Cuts the audio into phrases with a simple energy-based voice detector, and transcribes each phrase."""
    PRE_ROLL_BLOCKS = 3  # Audio kept from before the speech started, so the first syllable is not cut
    END_SILENCE_BLOCKS = 8  # Silence that ends a phrase
    MIN_VOICED_BLOCKS = 3  # Shorter sounds (clicks, coughs) are ignored
    MAX_PHRASE_BLOCKS = 300  # 30 s - Whisper's window
    CALIBRATION_BLOCKS = 10

    def __init__(self, model_path: Path, language: str | None):
        from faster_whisper import WhisperModel
        self.model = WhisperModel(str(model_path), device="cpu", compute_type="int8",
                                  cpu_threads=max(1, (os.cpu_count() or 2) // 2))
        self.language = language
        self.noise_level: float | None = None
        self.calibration: list[float] = []
        self.pre_roll: deque[np.ndarray] = deque(maxlen=self.PRE_ROLL_BLOCKS)
        self.phrase: list[np.ndarray] = []
        self.voiced_blocks = 0
        self.silent_blocks = 0

    def feed(self, chunk: bytes) -> str | None:
        samples = np.frombuffer(chunk, dtype=np.int16)
        rms = float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))

        if self.noise_level is None:  # Learn the background noise level during the first second
            self.calibration.append(rms)
            if len(self.calibration) >= self.CALIBRATION_BLOCKS:
                self.noise_level = float(np.median(self.calibration))
            return None

        is_voiced = rms > max(3 * self.noise_level, 300)
        if not self.phrase:
            if not is_voiced:
                self.noise_level = 0.95 * self.noise_level + 0.05 * rms  # Follow slow changes of the background
                self.pre_roll.append(samples)
                return None
            self.phrase = list(self.pre_roll)
            self.pre_roll.clear()
            self.voiced_blocks = self.silent_blocks = 0

        self.phrase.append(samples)
        if is_voiced:
            self.voiced_blocks += 1
            self.silent_blocks = 0
        else:
            self.silent_blocks += 1
        if self.silent_blocks < self.END_SILENCE_BLOCKS and len(self.phrase) < self.MAX_PHRASE_BLOCKS:
            return None

        phrase, self.phrase = self.phrase, []
        if self.voiced_blocks < self.MIN_VOICED_BLOCKS:
            return None
        return self.transcribe(np.concatenate(phrase))

    def transcribe(self, samples: np.ndarray) -> str:
        audio = samples.astype(np.float32) / 32768
        # vad_filter drops non-speech parts, which otherwise make Whisper hallucinate text out of noise.
        segments, _ = self.model.transcribe(audio, language=self.language, beam_size=5, vad_filter=True,
                                            condition_on_previous_text=False)
        return " ".join(segment.text.strip() for segment in segments)


def _is_vosk_model(model_path: Path) -> bool:
    return (model_path / "am").is_dir() or (model_path / "conf" / "model.conf").is_file()


def start_voice_listener(model_path: str | Path, command_map: dict[str, Callable] | None = None,
                         language: str | None = None, print_speech: bool = True):
    """
    Listen to the default microphone forever (Ctrl+C to stop) and run the commands that are said.

    model_path: a Vosk model folder, or a faster-whisper (CTranslate2) model folder.
    command_map: phrase -> function, added to DEFAULT_COMMANDS.
    language: Whisper language code (e.g. "he", "en"); None auto-detects. Ignored by Vosk models.
    """
    model_path = Path(model_path)
    command_map = {**DEFAULT_COMMANDS, **(command_map or {})}
    command_map = {k.lower(): v for k, v in command_map.items()}

    print(f"Loading speech model from {model_path} ...")
    engine = _VoskEngine(model_path) if _is_vosk_model(model_path) else _WhisperEngine(model_path, language)
    audio_q: queue.Queue[bytes] = queue.Queue()

    def audio_callback(indata, frames, time, status):
        if status:
            print(f"[Audio status]: {status}")
        audio_q.put(bytes(indata))

    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE, dtype="int16", channels=1,
                           callback=audio_callback):
        print(f"Listening for: {', '.join(command_map)}  (Ctrl+C to stop)")
        try:
            while True:
                text = engine.feed(audio_q.get())
                if not text or not text.strip():
                    continue
                text = text.strip()
                if print_speech:
                    print(f"[Recognized]: {text}")
                run_command(text, command_map)
        except KeyboardInterrupt:
            print("Stopped listening.")
