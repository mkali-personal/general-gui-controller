"""Give every image in the LyX document that is open right now a standard size - in place.

Images that already have a size (width, height or scale) are left as they are. Every other image gets:
  * width 65col%  - its size in the exported PDF;
  * lyxscale N    - its size on screen in LyX, as a percent of the image's own pixel size, chosen so
                    the image shows about LYX_DISPLAY_WIDTH_PIXELS wide (only for image types Pillow
                    can read, e.g. png / jpg; others keep LyX's default). An existing lyxscale is kept.

How it works with the running LyX:
  1. The open document is read from the LyX window title, e.g.
     "Ex2.lyx (~\\Courses\\Optical systems design)* - LyX" - the '*' means unsaved changes.
  2. LyX is told to save (through the LyX server, Tools > Preferences > Paths > LyXServer pipe), and
     the script waits until the '*' is gone - so unsaved work is kept, and LyX will not overwrite the
     edit on its next save.
  3. The file is edited, and - once LyX shows "(modified externally)" in its title - LyX is told to
     reload it. If that does not work, LyX's own message about the changed file offers to reload.
LyX's answers on the server pipe are not used: on Windows LyX can hand a new reader an answer meant
for an earlier command, so only sending commands is reliable.
"""
import ctypes
import os
import re
import time
from ctypes import wintypes

from PIL import Image

LYX_SERVER_PIPE = "\\\\.\\pipe\\" + os.path.join(os.environ['APPDATA'], "LyX2.5", "lyxpipe")  # LyX's default
PDF_WIDTH = '65col%'
LYX_DISPLAY_WIDTH_PIXELS = 600
LYXSCALE_RANGE = (5, 100)  # never enlarge images beyond their own size on screen
SIZE_KEYS = ('width', 'height', 'scale')
GRAPHICS_INSET_PATTERN = re.compile(r'(\\begin_inset Graphics\n)(.*?)(\n\\end_inset)', re.DOTALL)
# e.g. "Ex2.lyx (~\Courses)* - LyX" or "Ex2.lyx (~\Courses) (modified externally) - LyX"
LYX_TITLE_PATTERN = re.compile(r'^(?P<name>.+?\.lyx) \((?P<folder>[^()]+)\)(?P<unsaved>\*)?')
CLIENT_NAME = 'lyx_resize_images'
SAVE_TIMEOUT_SECONDS = 20
CHANGE_NOTICE_TIMEOUT_SECONDS = 10


# --- Talking to LyX ------------------------------------------------------------------------------

def lyx_window_titles() -> list[str]:
    """Titles of the visible windows of LyX.exe."""
    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    titles = []

    def on_window(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        process = kernel32.OpenProcess(0x1000, False, pid.value)  # PROCESS_QUERY_LIMITED_INFORMATION
        if process:
            exe = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(1024)
            kernel32.QueryFullProcessImageNameW(process, 0, exe, ctypes.byref(size))
            kernel32.CloseHandle(process)
            if os.path.basename(exe.value).lower() == 'lyx.exe':
                title = ctypes.create_unicode_buffer(1024)
                user32.GetWindowTextW(hwnd, title, 1024)
                titles.append(title.value)
        return True

    user32.EnumWindows(ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(on_window), 0)
    return titles


def open_lyx_document() -> tuple[str, bool]:
    """Full path of the document shown in the LyX window, and whether it has unsaved changes."""
    for title in lyx_window_titles():
        match = LYX_TITLE_PATTERN.match(title)
        if match:
            folder = os.path.expanduser(match['folder'])
            return os.path.join(folder, match['name']), match['unsaved'] is not None
    raise RuntimeError("[ERROR] No LyX window with an open document was found.")


def wait_until_title_says(text: str, present: bool, timeout: float) -> bool:
    """Wait until `text` appears in (present=True) or disappears from the LyX window title."""
    deadline = time.time() + timeout
    while any(text in title for title in lyx_window_titles()) != present:
        if time.time() > deadline:
            return False
        time.sleep(0.2)
    return True


def send_lyx_command(function: str, argument: str = '', timeout: float = 5) -> None:
    """Send a LyX function to the running LyX. Retries while LyX's pipe is busy."""
    deadline = time.time() + timeout
    while True:
        try:
            with open(LYX_SERVER_PIPE + '.in', 'w', encoding='utf-8') as pipe_in:
                pipe_in.write(f"LYXCMD:{CLIENT_NAME}:{function}:{argument}\n")
            return
        except OSError:
            if time.time() > deadline:
                raise RuntimeError(f"[ERROR] Could not send '{function}' to LyX - is the LyX server on?")
            time.sleep(0.2)


# --- Resizing ------------------------------------------------------------------------------------

def lyxscale_for(image_path: str) -> int | None:
    """The lyxscale that shows the image about LYX_DISPLAY_WIDTH_PIXELS wide, or None if unreadable."""
    try:
        with Image.open(image_path) as image:
            pixel_width = image.width
    except (OSError, ValueError):
        return None
    scale = round(100 * LYX_DISPLAY_WIDTH_PIXELS / pixel_width)
    return max(LYXSCALE_RANGE[0], min(LYXSCALE_RANGE[1], scale))


def resize_images(lyx_text: str, lyx_dir: str) -> tuple[str, int, int]:
    """Return the LyX text with unsized images sized, and the counts of resized and skipped images."""
    counts = {'resized': 0, 'skipped': 0}

    def resize_inset(match: re.Match) -> str:
        begin, body, end = match.groups()
        lines = body.split('\n')
        keys = {line.strip().split(' ', 1)[0] for line in lines}
        if keys & set(SIZE_KEYS):
            counts['skipped'] += 1
            return match.group(0)
        counts['resized'] += 1
        filename = next(line.strip().split(' ', 1)[1] for line in lines if line.strip().startswith('filename '))
        new_lines = [line for line in lines if line.strip()]  # LyX keeps an empty line before \end_inset
        if 'lyxscale' not in keys:
            scale = lyxscale_for(os.path.join(lyx_dir, filename.strip('"')))
            if scale is not None:
                new_lines.append(f'\tlyxscale {scale}')
        new_lines.append(f'\twidth {PDF_WIDTH}')
        return begin + '\n'.join(new_lines) + '\n' + end

    new_text = GRAPHICS_INSET_PATTERN.sub(resize_inset, lyx_text)
    return new_text, counts['resized'], counts['skipped']


# --- Main ----------------------------------------------------------------------------------------

def main() -> None:
    lyx_file, unsaved = open_lyx_document()
    print(f"Open LyX document: {lyx_file}")
    if unsaved:
        send_lyx_command('buffer-write')
        deadline = time.time() + SAVE_TIMEOUT_SECONDS
        while open_lyx_document()[1]:
            if time.time() > deadline:
                raise RuntimeError("[ERROR] LyX did not save the document - nothing was changed.")
            time.sleep(0.2)

    with open(lyx_file, encoding='utf-8', newline='') as file:
        raw_text = file.read()
    line_ending = '\r\n' if '\r\n' in raw_text else '\n'  # LyX on Windows writes \r\n; keep whatever the file has
    text = raw_text.replace('\r\n', '\n')
    new_text, resized, skipped = resize_images(text, os.path.dirname(lyx_file))
    if resized:
        with open(lyx_file, 'w', encoding='utf-8', newline=line_ending) as file:
            file.write(new_text)
        # LyX notices the change a second or two later; a reload sent before that is undone by the notice.
        wait_until_title_says('modified externally', present=True, timeout=CHANGE_NOTICE_TIMEOUT_SECONDS)
        send_lyx_command('buffer-reload')
        if not wait_until_title_says('modified externally', present=False, timeout=5):
            print("LyX did not reload by itself - click 'Reload' in LyX's message about the changed file.")
    print(f"Resized {resized} image(s), left {skipped} image(s) that already had a size.")


if __name__ == '__main__':
    main()
