"""
Say "log <something>" / "notebook <something>" (or "רשום <something>") to append "* Voice log: <something>" to local_config.NOTES_PATH.

uv run voice_notes.py            -> default model (local_config.PATH_STT_MODEL)
uv run voice_notes.py en-large   -> large English model (Vosk)
uv run voice_notes.py en-whisper -> English Whisper model (most accurate, ~13 s per phrase)
uv run voice_notes.py he         -> Hebrew model
"""
import sys

from core.kalifcode import start_voice_listener
from local_config import PATH_STT_MODEL, STT_MODEL_EN, STT_MODEL_EN_LARGE, STT_MODEL_EN_WHISPER, STT_MODEL_HE

MODELS = {"default": (PATH_STT_MODEL, None), "en": (STT_MODEL_EN, "en"), "en-large": (STT_MODEL_EN_LARGE, "en"),
          "en-whisper": (STT_MODEL_EN_WHISPER, "en"), "he": (STT_MODEL_HE, "he")}

choice = sys.argv[1] if len(sys.argv) > 1 else "default"
if choice not in MODELS:
    sys.exit(f"Unknown model '{choice}', choose one of: {', '.join(MODELS)}")
model_path, language = MODELS[choice]
start_voice_listener(model_path=model_path, language=language)
