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

# Audio callback
def audio_callback(indata, frames, time, status):
    if status:
        print(f"[Audio status]: {status}")
    audio_q.put(bytes(indata))


def recognize_loop(command_map):
    rec = vosk.KaldiRecognizer(model, 16000)
    while True:
        data = audio_q.get()
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text = result.get("text", "").lower()
            if text:
                print(f"[Recognized]: {text}")
                if text in command_map:
                    try:
                        command_map[text]()
                    except Exception as e:
                        print(f"[ERROR running command]: {e}")


# Entry point — pass your command_map here
def start_voice_listener(command_map: dict):
    threading.Thread(target=recognize_loop, args=(command_map,), daemon=True).start()

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=audio_callback):
        print("🎤 Listening for commands...")
        while True:
            pass  # keep main thread alive



if __name__ == "__main__":
    # Command function map
    def foo():
        print("hello world")

    # Example command map
    start_voice_listener(command_map={
        "print": foo
    })