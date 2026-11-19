"""Create local_config.py with dummy values for you to fill in.

local_config.py holds personal settings (user names, passwords, file paths)
and is listed in .gitignore, so it is never committed. Run this script once on
a new computer, then open local_config.py and replace the dummy values.

If local_config.py already exists, it is not overwritten: only settings that
are missing from it are added at the end, with dummy values.
"""
import re
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "local_config.py"

# name -> (dummy value as it should appear in the file, comment explaining it)
SETTINGS = {
    "TAFNIT_USER_NAME": ('"your_user_name"',
                         "Tafnit / Weizmann login user name (used by kalirkosh.py, kalirkosh_web.py, open_moodle.py)"),
    "TAFNIT_PASSWORD": ('"your_password"',
                        "Tafnit / Weizmann login password (used by kalirkosh.py, kalirkosh_web.py, open_moodle.py)"),
    "REPETETIV_FOOD_ORDER_PATH": (r'r"C:\path\to\food order.xlsx"',
                                  "Full path to the quote file used for the repeating food order (used by kalirkosh.py, kalirkosh_web.py)"),
    "PATH_STT_MODEL": (r'r"C:\path\to\vosk-model-folder"',
                       "Folder of the Vosk speech-to-text model (used by core/kalifcode.py)"),
}


def setting_lines(names):
    lines = []
    for name in names:
        value, comment = SETTINGS[name]
        lines.append(f"# {comment}")
        lines.append(f"{name} = {value}")
        lines.append("")
    return "\n".join(lines)


def main():
    if not CONFIG_PATH.exists():
        header = "# Personal settings. This file is in .gitignore - do not commit it.\n\n"
        CONFIG_PATH.write_text(header + setting_lines(SETTINGS), encoding="utf-8")
        print(f"Created {CONFIG_PATH}")
        print("Open it and replace the dummy values with your own.")
        return

    existing = CONFIG_PATH.read_text(encoding="utf-8")
    missing = [name for name in SETTINGS
               if not re.search(rf"^{name}\s*=", existing, flags=re.MULTILINE)]
    if not missing:
        print(f"{CONFIG_PATH} already exists and has all settings. Nothing changed.")
        return

    with CONFIG_PATH.open("a", encoding="utf-8") as f:
        if not existing.endswith("\n"):
            f.write("\n")
        f.write("\n" + setting_lines(missing))
    print(f"{CONFIG_PATH} already exists. Added missing settings with dummy values:")
    for name in missing:
        print(f"  {name}")
    print("Open it and replace those dummy values with your own.")


if __name__ == "__main__":
    main()
