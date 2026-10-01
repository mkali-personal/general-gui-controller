# General GUI controller

## Installation (with uv)
The project is managed with [uv](https://docs.astral.sh/uv/) — a fast Python package and environment manager that replaces pip + venv. Dependencies are declared in `pyproject.toml` and pinned exactly in `uv.lock`, so every machine gets the same environment.

1. **Install uv** (one time, no Python required beforehand):
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
   (On Linux/macOS: `curl -LsSf https://astral.sh/uv/install.sh | sh`)

2. **Create the virtual environment and install everything**, from the project root:
   ```powershell
   uv sync
   ```
   This single command reads `.python-version` (Python 3.11), downloads that Python if it's missing, creates `.venv/`, and installs all locked dependencies. It typically takes seconds thanks to uv's global cache.

3. **Run scripts** through the environment (no manual activation needed):
   ```powershell
   uv run kalirkosh.py
   ```
   Or activate the venv classically: `.venv\Scripts\activate` (Windows) / `source .venv/bin/activate` (Linux/macOS) and use `python` as usual.

**Adding/updating a dependency:** `uv add <package>` (updates `pyproject.toml` and `uv.lock` automatically). After pulling changes that touch the lockfile, just run `uv sync` again.


The module uses simple image recognition (cv2.matchTemplate) to find the location of a given image on the screen, and act on it (click, type, paste, etc...). It can be used to automate tasks by locating buttons or other UI elements in applications.
OCR was used but didn't perform well, so it was deprecated.
Since it uses image recognition, it can handle any application, not just web browsers.

To record a patch of the screen, to be searched for later, use the `core.general_gui_controller.record_gui_template` function (or just take a print screen and crop it).

`detect_template` can search for the next types of templates:
1) A simple image (the coordinate of the center of the image is returned).
2) A relative coordinate with respect to a simple image (the coordinate of the center of the image plus the relative offset is returned).
3) A list of images (the location of first one that is found will be used)
4) A complex template\list of complex templates, where first one is being searched for, and then the second image is searched for in the area around the first image. The coordinate of the center of the second image is returned.
5) A sorter to handle multiple detections (e.g., to return the lowest one, or the one closest to a given point).

`detect_template_and_act`:
Combines `detect_template` with a set of actions to be performed when the template is found. Actions can include mouse clicks, keyboard input, waiting for a certain time.

`kalifcode.start_voice_listener`:
Continuously listens (offline) for a voice command, and when it hears defined keywords, it runs a corresponding function. - good for work in the lab where the hands are pre-occupied.
Built-in commands: "log <text>" / "notebook <text>" / "רשום <text>" appends `* Voice log: <text>` to the markdown file `NOTES_PATH`. `type_text` (paste at the cursor) can be added with `command_map={"type": type_text}`.
The model folder passed to `start_voice_listener(model_path, ...)` selects the engine:
* [Vosk](https://alphacephei.com/vosk/models) models (e.g. `vosk-model-en-us-0.22-lgraph`, `vosk-model-en-us-0.22`) - real time, English, best for short fixed commands.
* faster-whisper (CTranslate2) models, e.g. [ivrit-ai/whisper-large-v3-turbo-ct2](https://huggingface.co/ivrit-ai/whisper-large-v3-turbo-ct2) for Hebrew - much more accurate on free speech, but transcribes each phrase after you stop talking (~13 s per phrase on the lab PC's CPU). Needs an up-to-date [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) - older ones make it crash on load.

Setup: put the models in `models/` and set their paths and `NOTES_PATH` in `local_config.py`. Then run `uv run voice_notes.py` (default model), `uv run voice_notes.py en-large`, `uv run voice_notes.py en-whisper` or `uv run voice_notes.py he`.

### Note:
The directory is organized such that the core of the code is in the `core` folder, while the actual automations files are in the main folder. This is intentional, and allows to run the script from the main folder both from the IDE and directly from the os system, without having to reconfigure the current working directory. 
