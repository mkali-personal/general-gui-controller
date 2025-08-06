import queue
import sounddevice as sd
import vosk
import json
import threading

# Load offline Vosk model
vosk_model_path = "utilities/automations/models/vosk-model-small-en-us-0.15"  # vosk-model-en-us-0.22-lgraph
model = vosk.Model(vosk_model_path)

# Queue to receive audio data
audio_q = queue.Queue()

# Command function map
def foo():
    print("hello world")

command_map = {
    "print": foo
}

# Audio callback
def audio_callback(indata, frames, time, status):
    if status:
        print(f"[Audio status]: {status}")
    audio_q.put(bytes(indata))

# Continuous STT processing thread
def recognize_loop():
    rec = vosk.KaldiRecognizer(model, 16000)
    while True:
        data = audio_q.get()
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text = result.get("text", "").lower()
            if text:
                print(f"[Recognized]: {text}")
                if text in command_map:
                    command_map[text]()  # Run the matched command
        else:
            # Optional: can parse partial results here if desired
            pass

# Start everything
def start_voice_listener():
    # Launch STT thread
    threading.Thread(target=recognize_loop, daemon=True).start()

    # Start audio stream
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=audio_callback):
        print("🎤 Listening... (say 'print' to run foo())")
        while True:
            pass  # Keep the main thread alive


start_voice_listener()