import os
import threading
import time
from contextlib import contextmanager
from time import sleep
from tkinter import Tk, filedialog
from typing import Optional, Tuple, Callable, Union, List  # noqa: F401  (leaked to scripts via `import *`)
from warnings import warn

import cv2
import numpy as np
import pyautogui
import pyperclip
from PIL import ImageGrab
from plyer import notification
from pynput import keyboard

# Constants
GENERAL_GUI_CONTROLLER_TEMPLATES_PATH = r"ggc-templates"
DEFAULT_MINIMAL_CONFIDENCE = 0.95
DEFAULT_MULTIPLE_MATCHES_TOLERANCE = 0.03
DETECTION_RETRY_SLEEP_SECONDS = 0.2
# Scales to try when matching templates, ordered so scales closest to 1.0 are tried first.
TEMPLATE_SCALES = sorted(np.linspace(0.8, 1.2, num=5), key=lambda s: abs(s - 1.0))
# Global hotkey that aborts the current template detection (and any action depending on it).
SKIP_HOTKEY = '<ctrl>+<alt>+<f12>'
SKIP_HOTKEY_DISPLAY = 'Ctrl+Alt+F12'


def notify_main_screen():
    """Show a desktop notification telling the user which screen the automation will control."""
    notification.notify(
        title="This is your main screen",
        message="Make sure the GUI you wish to control is visible on this screen.",
        timeout=5,
    )


def pick_file(initialdir: str | None = None,
              filetypes: tuple = (("All files", "*.*"),)):
    """Open native file dialog and return selected path ('' if canceled)."""
    root = Tk()
    root.withdraw()  # hide the empty root window
    try:
        return filedialog.askopenfilename(initialdir=initialdir, filetypes=filetypes)
    finally:
        root.destroy()


# --- Skip-detection hotkey ---------------------------------------------------
# pynput's GlobalHotKeys listener runs in its own background thread, so the
# synchronous detection loops below only need to poll this event between match
# attempts - no async machinery required.
_skip_requested = threading.Event()
_skip_listener: keyboard.GlobalHotKeys | None = None
_skip_listener_depth = 0
_skip_lock = threading.Lock()


@contextmanager
def _skip_hotkey_armed():
    """Arm the skip hotkey while a detection/waiting loop runs.

    Reference-counted so nested loops (e.g. wait_for_template_to_disappear
    calling detect_template) share a single keyboard hook.
    """
    global _skip_listener, _skip_listener_depth
    with _skip_lock:
        if _skip_listener_depth == 0:
            _skip_requested.clear()
            _skip_listener = keyboard.GlobalHotKeys({SKIP_HOTKEY: _skip_requested.set})
            _skip_listener.start()
        _skip_listener_depth += 1
    try:
        yield
    finally:
        with _skip_lock:
            _skip_listener_depth -= 1
            if _skip_listener_depth == 0:
                _skip_listener.stop()
                _skip_listener = None
                _skip_requested.clear()


def _skip_was_requested(template) -> bool:
    """Consume a pending skip request, if any, and report it to the user."""
    if _skip_requested.is_set():
        _skip_requested.clear()
        print(f"\n[SKIP] {SKIP_HOTKEY_DISPLAY} pressed - skipping detection of '{template}'.")
        return True
    return False


def _handle_not_found(message: str, exception_if_not_found: bool, warn_if_not_found: bool) -> None:
    if exception_if_not_found:
        raise RuntimeError(message)
    if warn_if_not_found:
        warn(message)
    return None
# -----------------------------------------------------------------------------


def take_screenshot(screenshot: np.ndarray | None = None, grayscale_mode: bool = True) -> np.ndarray:
    """Capture the screen (optionally grayscale).

    If `screenshot` is provided it is returned untouched (pass-through so callers
    can reuse one capture for several detections); `grayscale_mode` only applies
    to freshly captured screenshots.
    """
    if screenshot is None:
        screenshot = np.array(ImageGrab.grab())
        if grayscale_mode:
            screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)
    return screenshot


def minimize_current_window():
    """Minimize the current window using keyboard shortcuts (Win+Down)."""
    keyboard_controller = keyboard.Controller()
    keyboard_controller.press(keyboard.Key.cmd)
    keyboard_controller.press(keyboard.Key.down)
    time.sleep(0.05)
    keyboard_controller.release(keyboard.Key.down)
    keyboard_controller.release(keyboard.Key.cmd)


def get_cursor_position(target_name: str) -> tuple[float, float] | None:
    """Prompt the user to place the cursor and record its position on left-Ctrl press.

    Returns None if the user pressed Escape instead.
    """
    print(f"Place the cursor over the\n{target_name}\nand press the left 'Ctrl' on the keyboard")
    position = None

    def on_press(key):
        nonlocal position
        if key == keyboard.Key.ctrl_l:
            position = pyautogui.position()
            print(position)
            return False
        if key == keyboard.Key.esc:
            position = None
            print('User pressed Escape, exiting without recording position.')
            return False

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
    print(f"Cursor position recorded for {target_name}: {position}\n")
    return position


def get_relative_point_position(x, y, w, h, relative_position: tuple[float, float] | None = None):
    """Calculate a screen point relative to a bounding box.

    Convention (matches record_gui_template): `relative_position` is (dx, dy) in
    fractions of the box size, measured from the box's BOTTOM-LEFT corner with the
    y-axis pointing UP. E.g. (0, 0) is the bottom-left corner, (0.5, 0.5) the
    center, (1, 1) the top-right corner; values outside [0, 1] land outside the box.
    If None, returns the box center.
    """
    if relative_position:
        return x + w * relative_position[0], (y + h) - h * relative_position[1]
    return x + w / 2, y + h / 2


def wait_for_template(input_template: str,
                      verbose: bool = True,  # kept for backward compatibility; dots are printed either way
                      max_searching_time: float | None = None):
    """Wait for a template to appear. Thin wrapper around detect_template.

    Returns the found position, or None if `max_searching_time` elapsed.
    """
    max_waiting_time = np.inf if max_searching_time is None else max_searching_time
    return detect_template(input_template,
                           max_waiting_time_seconds=max_waiting_time,
                           warn_if_not_found=False)


def load_templates_list(template_pairs: list[tuple], grayscale_mode: bool = True, return_all: bool = True) -> list:
    """Load (primary, secondary) template pairs, expanding name-prefix matches into all combinations."""
    output_list = []
    for template_pair in template_pairs:
        sublist_1 = load_template(template_pair[0], grayscale_mode, return_all)
        sublist_2 = load_template(template_pair[1], grayscale_mode, return_all)
        if isinstance(sublist_1, list) and isinstance(sublist_2, list):
            if len(sublist_1) != len(sublist_2):
                raise ValueError("If both input_templates and secondary_templates are lists, "
                                 "they must have the same length.")
            output_list.extend(zip(sublist_1, sublist_2))
        elif isinstance(sublist_1, list):
            output_list.extend((s_1, sublist_2) for s_1 in sublist_1)
        elif isinstance(sublist_2, list):
            output_list.extend((sublist_1, s_2) for s_2 in sublist_2)
        else:
            output_list.append((sublist_1, sublist_2))
    return output_list


def load_template(template: Union[str, np.ndarray], grayscale_mode: bool = True, return_all: bool = True) -> Union[np.ndarray, list[np.ndarray]]:
    """Load a template image by file name (or pass an array through unchanged).

    With return_all=True, every file in the templates directory whose name starts
    with `template` is loaded (a single match is returned unwrapped).
    """
    if not isinstance(template, str):
        # Assume an image array is already in the desired format.
        return template

    if return_all:
        templates = []
        for fname in sorted(os.listdir(GENERAL_GUI_CONTROLLER_TEMPLATES_PATH)):
            if fname.startswith(template):
                template_path = os.path.join(GENERAL_GUI_CONTROLLER_TEMPLATES_PATH, fname)
                arr = cv2.imread(template_path, cv2.IMREAD_COLOR)
                if arr is None:
                    raise FileNotFoundError(f"Could not read image file: {template_path} "
                                            f"(current working directory: {os.getcwd()})")
                if grayscale_mode:
                    arr = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
                templates.append(arr)
        if not templates:
            raise FileNotFoundError(f"No files found starting with: {template} in "
                                    f"{GENERAL_GUI_CONTROLLER_TEMPLATES_PATH}, "
                                    f"current working directory: {os.getcwd()}")
        if len(templates) == 1:
            return templates[0]
        return templates

    template_path = os.path.join(GENERAL_GUI_CONTROLLER_TEMPLATES_PATH, template)
    if os.path.splitext(template_path)[1] == "":
        template_path += '.png'
    arr = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if arr is None:
        raise FileNotFoundError(f"File: {template_path} not found, "
                                f"current working directory: {os.getcwd()}")
    if grayscale_mode:
        arr = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
    return arr


def detect_single_template(
        template: Union[str, np.ndarray],
        secondary_template: Optional[Union[str, np.ndarray]] = None,
        secondary_template_direction: str | None = None,
        relative_position: tuple[float, float] | None = None,
        minimal_confidence: float = DEFAULT_MINIMAL_CONFIDENCE,
        exception_if_not_found: bool = False,
        warn_if_not_found: bool = True,
        screenshot: np.ndarray | None = None,
        grayscale_mode: bool = True,
        multiple_matches_sorter: Optional[Union[Callable, np.ndarray]] = None,
        multiple_matches_tolerance: float = DEFAULT_MULTIPLE_MATCHES_TOLERANCE,
) -> tuple[float, float] | None:
    """Match a single template against one screenshot (no retry loop).

    If `multiple_matches_sorter` is provided, all matches whose score is both above
    `minimal_confidence` and within `multiple_matches_tolerance` of the best score
    are collected, and the sorter picks among them: either a callable used as a
    sort key over (x, y) click positions, or a direction vector (np.ndarray) -
    the match furthest along that direction wins (screen y-axis pointing up).
    Otherwise the single best-scoring match is returned.
    """
    if (secondary_template is None) != (secondary_template_direction is None):
        raise ValueError("If secondary_template is provided, "
                         "secondary_template_direction must also be provided (and vice versa).")

    if secondary_template is not None:
        if multiple_matches_sorter is not None:
            warn("multiple_matches_sorter is ignored when searching for a nearby secondary_template")
        return detect_complex_template(template_a=template, template_b=secondary_template,
                                       direction=secondary_template_direction,
                                       screenshot=screenshot,
                                       grayscale_mode=grayscale_mode,
                                       minimal_confidence=minimal_confidence,
                                       exception_if_not_found=exception_if_not_found,
                                       warn_if_not_found=warn_if_not_found,
                                       relative_position=relative_position)

    if isinstance(multiple_matches_sorter, np.ndarray):
        direction_vector = np.array([multiple_matches_sorter[0], -multiple_matches_sorter[1]])
        multiple_matches_sorter = lambda point: -np.array(point) @ direction_vector

    template = load_template(template, grayscale_mode=grayscale_mode)
    screenshot = take_screenshot(screenshot=screenshot, grayscale_mode=grayscale_mode)

    tH, tW = template.shape[:2]
    if tH > screenshot.shape[0] or tW > screenshot.shape[1]:
        return _handle_not_found(f"[ERROR] Template ({tW}x{tH}) is larger than the screenshot "
                                 f"({screenshot.shape[1]}x{screenshot.shape[0]}).",
                                 exception_if_not_found, warn_if_not_found)

    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val < minimal_confidence:
        return _handle_not_found(f"[ERROR] Best match score {max_val:.3f} is below "
                                 f"minimal_confidence {minimal_confidence:.3f}.",
                                 exception_if_not_found, warn_if_not_found)

    if multiple_matches_sorter is None:
        x, y = max_loc
        return get_relative_point_position(x, y, tW, tH, relative_position)

    ys, xs = np.where((result >= minimal_confidence) & (result >= max_val - multiple_matches_tolerance))
    candidate_points = [get_relative_point_position(x, y, tW, tH, relative_position)
                        for x, y in zip(xs, ys)]
    return min(candidate_points, key=multiple_matches_sorter)


def detect_template(template: Union[str, list[str]],
                    secondary_template: Optional[Union[str, list[str]]] = None,
                    secondary_template_direction: str | None = None,
                    relative_position: tuple[float, float] | None = None,
                    minimal_confidence: float = DEFAULT_MINIMAL_CONFIDENCE,
                    exception_if_not_found: bool = False,
                    warn_if_not_found: bool = True,
                    grayscale_mode: bool = True,
                    max_waiting_time_seconds: float = np.inf,
                    multiple_matches_sorter: Optional[Union[Callable, np.ndarray]] = None,
                    multiple_matches_tolerance: float = DEFAULT_MULTIPLE_MATCHES_TOLERANCE,
                    all_files_name_matching: bool = True) -> tuple[float, float] | None:
    """Detect a template on screen, retrying until found, timed out, or skipped.

    Retries screenshots until the template appears or `max_waiting_time_seconds`
    elapses (0 = single attempt). Multiple template files (list, or several files
    sharing a name prefix when all_files_name_matching=True) and multiple scales
    (TEMPLATE_SCALES) are tried on every screenshot.

    While searching, pressing SKIP_HOTKEY (Ctrl+Alt+F12) aborts the detection and
    returns None immediately, without warning or raising - so a script stuck on a
    template that never appears can be nudged forward manually.
    """
    if isinstance(template, list) and isinstance(secondary_template, list) \
            and len(template) != len(secondary_template):
        raise ValueError("If both template and secondary_template are lists, "
                         "they must have the same length.")
    if exception_if_not_found and bool(max_waiting_time_seconds):
        raise ValueError("Cannot combine exception_if_not_found=True with a nonzero "
                         "max_waiting_time_seconds: use max_waiting_time_seconds=0 for a "
                         "single attempt that raises on failure.")

    if isinstance(template, list) and not isinstance(secondary_template, list):
        secondary_template = [secondary_template] * len(template)
    if not isinstance(template, list) and isinstance(secondary_template, list):
        template = [template] * len(secondary_template)
    if not isinstance(template, list):
        template = [template]
    if not isinstance(secondary_template, list):
        secondary_template = [secondary_template]

    template_pairs = load_templates_list(list(zip(template, secondary_template)),
                                         grayscale_mode=grayscale_mode,
                                         return_all=all_files_name_matching)

    start_time = time.time()
    dot_count = 0
    with _skip_hotkey_armed():
        while True:
            if _skip_was_requested(template):
                return None
            if dot_count == 1:
                print(f"(Press {SKIP_HOTKEY_DISPLAY} to skip waiting for this template)")
            if dot_count > 0:
                dots = '.' * (dot_count % 4)
                print(f"Waiting for template '{template}' to appear{dots}   ", end="\r")
            screenshot = take_screenshot(grayscale_mode=grayscale_mode)
            for scale in TEMPLATE_SCALES:
                for template_1, template_2 in template_pairs:
                    if _skip_was_requested(template):
                        return None
                    if scale != 1:
                        template_1 = cv2.resize(template_1, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
                        if template_2 is not None:
                            template_2 = cv2.resize(template_2, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
                    detection_results = detect_single_template(
                        template=template_1,
                        secondary_template=template_2,
                        secondary_template_direction=secondary_template_direction,
                        relative_position=relative_position,
                        minimal_confidence=minimal_confidence,
                        exception_if_not_found=False,
                        warn_if_not_found=False,
                        screenshot=screenshot,
                        grayscale_mode=False,  # already grayscale if needed
                        multiple_matches_sorter=multiple_matches_sorter,
                        multiple_matches_tolerance=multiple_matches_tolerance,
                    )
                    if detection_results is not None:
                        print(f"\nFound template '{template}' at position {detection_results}")
                        return detection_results[0], detection_results[1]
            if max_waiting_time_seconds == 0 or (time.time() - start_time) > max_waiting_time_seconds:
                break
            dot_count += 1
            sleep(DETECTION_RETRY_SLEEP_SECONDS)

    return _handle_not_found(f"[ERROR] Failed to fit template: {template}",
                             exception_if_not_found, warn_if_not_found)


def wait_for_template_to_disappear(template: Union[str, list[str]],
                                   max_waiting_time_seconds: float = np.inf,
                                   sleep_after_iteration_seconds: float = DETECTION_RETRY_SLEEP_SECONDS,
                                   **kwargs):
    """Block until the template is no longer detected (or timeout / skip hotkey)."""
    start_time = time.time()
    dot_count = 0
    with _skip_hotkey_armed():
        while True:
            if _skip_requested.is_set():
                _skip_requested.clear()
                print(f"\n[SKIP] {SKIP_HOTKEY_DISPLAY} pressed - no longer waiting for "
                      f"'{template}' to disappear.")
                return
            if dot_count > 0:
                dots = '.' * (dot_count % 4)
                print(f"Waiting for template '{template}' to disappear{dots}   ", end="\r")
            detected_position = detect_template(template, max_waiting_time_seconds=0,
                                                exception_if_not_found=False,
                                                warn_if_not_found=False, **kwargs)
            if detected_position is None:
                print(f"\nTemplate '{template}' has disappeared")
                return
            if max_waiting_time_seconds == 0 or (time.time() - start_time) > max_waiting_time_seconds:
                return
            dot_count += 1
            sleep(sleep_after_iteration_seconds)


def detect_template_and_act(
        input_template: Optional[Union[str, list[str]]] = None,
        secondary_template: Optional[Union[str, list[str]]] = None,
        secondary_template_direction: str | None = None,
        relative_position: tuple[float, float] | None = None,
        minimal_confidence: float = DEFAULT_MINIMAL_CONFIDENCE,
        exception_if_not_found: bool = False,
        warn_if_not_found: bool = True,
        place_cursor: bool = True,
        click: bool = True,
        sleep_before_detection: float | None = None,
        sleep_after_action: float | None = None,
        text_to_paste=None,
        override_coordinates: tuple[float, float] | None = None,
        grayscale_mode: bool = True,
        max_waiting_time_seconds: float = np.inf,
        multiple_matches_sorter: Optional[Union[Callable, np.ndarray]] = None,
        multiple_matches_tolerance: float = DEFAULT_MULTIPLE_MATCHES_TOLERANCE,
) -> tuple[float, float] | None:
    """Detect a template and act at its location: click (and optionally paste text),
    or just move the cursor there (place_cursor=True, click=False).

    If the detection is skipped with the skip hotkey (or fails), no action is
    performed and None is returned. `override_coordinates` bypasses detection.
    """
    if text_to_paste is not None and not click:
        raise ValueError("Cannot paste text without clicking the target location first "
                         "(text_to_paste requires click=True).")
    if input_template is None and override_coordinates is None:
        raise ValueError("Either input_template or override_coordinates must be provided.")

    if sleep_before_detection is not None:
        sleep(sleep_before_detection)

    if override_coordinates is not None:
        coordinates = override_coordinates
    else:
        coordinates = detect_template(template=input_template, secondary_template=secondary_template,
                                      secondary_template_direction=secondary_template_direction,
                                      relative_position=relative_position, minimal_confidence=minimal_confidence,
                                      exception_if_not_found=exception_if_not_found,
                                      warn_if_not_found=warn_if_not_found, grayscale_mode=grayscale_mode,
                                      max_waiting_time_seconds=max_waiting_time_seconds,
                                      multiple_matches_sorter=multiple_matches_sorter,
                                      multiple_matches_tolerance=multiple_matches_tolerance)
    if coordinates is not None:
        if click:
            pyautogui.click(coordinates[0], coordinates[1])
            if text_to_paste is not None:
                paste_value(text_to_paste, coordinates, click=False, delete_existing=True)
        elif place_cursor:
            pyautogui.moveTo(coordinates[0], coordinates[1])

        if sleep_after_action is not None:
            sleep(sleep_after_action)
    return coordinates


def _expand_interval(lo: int, hi: int, needed: int, limit: int) -> tuple[int, int]:
    """
    Expand [lo, hi) to have length >= needed within [0, limit], preferring symmetric growth.
    If one side hits a boundary, reassign the remainder to the other side.
    Returns new (lo, hi) with 0 <= lo < hi <= limit (unless needed==0).
    """
    lo, hi = int(lo), int(hi)
    have = hi - lo
    if needed <= have:
        return lo, hi

    deficit = needed - have
    # Initial symmetric split
    extra_left = deficit // 2
    extra_right = deficit - extra_left

    # Apply left growth (moving lo to the left, i.e., decreasing lo)
    new_lo = max(0, lo - extra_left)
    used_left = lo - new_lo
    remaining = deficit - used_left

    # Apply right growth (moving hi to the right, i.e., increasing hi)
    new_hi = min(limit, hi + extra_right)
    used_right = new_hi - hi
    remaining -= used_right

    # Reassign leftover growth if one side was clamped
    if remaining > 0:
        cap_left = new_lo - 0  # how much more we can move left
        take_left = min(remaining, cap_left)
        new_lo -= take_left
        remaining -= take_left

        if remaining > 0:
            cap_right = limit - new_hi  # how much more we can move right
            take_right = min(remaining, cap_right)
            new_hi += take_right
            remaining -= take_right

    return new_lo, new_hi


def _compute_crop_excluding_template_a(x0: int, y0: int, w_a: int, h_a: int,
                                       direction: str,
                                       needed_perp: int,
                                       W: int, H: int) -> tuple[int, int, int, int] | None:
    """
    Build a crop that EXCLUDES template_a region and extends to the screen edge in `direction`.
    Then ensure the perpendicular span is at least `needed_perp` using _expand_interval.
    Returns (crop_x0, crop_y0, crop_x1, crop_y1) in screen coords, or None if impossible.
    """
    x1, y1 = x0 + w_a, y0 + h_a

    if direction == 'right':
        # Exclude template_a by starting at x1
        crop_x0 = min(max(x1, 0), W)
        crop_x1 = W
        # Perpendicular (y) starts as template_a's y-span
        crop_y0, crop_y1 = _expand_interval(max(0, y0), min(H, y1), needed_perp, H)

    elif direction == 'left':
        crop_x0 = 0
        crop_x1 = max(min(x0, W), 0)
        crop_y0, crop_y1 = _expand_interval(max(0, y0), min(H, y1), needed_perp, H)

    elif direction == 'down':
        crop_y0 = min(max(y1, 0), H)
        crop_y1 = H
        crop_x0, crop_x1 = _expand_interval(max(0, x0), min(W, x1), needed_perp, W)

    else:  # 'up'
        crop_y0 = 0
        crop_y1 = max(min(y0, H), 0)
        crop_x0, crop_x1 = _expand_interval(max(0, x0), min(W, x1), needed_perp, W)

    # Validate crop
    if crop_x1 - crop_x0 <= 0 or crop_y1 - crop_y0 <= 0:
        return None

    return crop_x0, crop_y0, crop_x1, crop_y1


def detect_complex_template(
        template_a: Union[str, np.ndarray],
        template_b: Union[str, np.ndarray],
        direction: str,
        screenshot: np.ndarray | None = None,
        grayscale_mode: bool = True,
        minimal_confidence: float = DEFAULT_MINIMAL_CONFIDENCE,
        exception_if_not_found: bool = False,
        warn_if_not_found: bool = True,
        relative_position: tuple[float, float] | None = None,
) -> tuple[float, float] | None:
    """
    Find template_b in a crop that starts immediately AFTER template_a in `direction`
    (crop EXCLUDES template_a). If the perpendicular span of template_a is too small
    to fit template_b, widen/tallen the crop symmetrically as allowed by the screen
    (and reassign any leftover expansion to the other side when clamped).

    Returns a point inside the found template_b (`relative_position` if provided,
    otherwise the center), or None on failure (unless exception_if_not_found=True).
    """
    direction = direction.lower()
    if direction not in {'up', 'down', 'left', 'right'}:
        raise ValueError("direction must be one of: 'up', 'down', 'left', 'right'")

    template_a = load_template(template_a, grayscale_mode=grayscale_mode)
    template_b = load_template(template_b, grayscale_mode=grayscale_mode)

    h_a, w_a = template_a.shape[:2]
    h_b, w_b = template_b.shape[:2]

    # Find template_a top-left once
    tl = detect_single_template(template=template_a, relative_position=(0.0, 1.0),
                                minimal_confidence=minimal_confidence,
                                exception_if_not_found=exception_if_not_found, warn_if_not_found=warn_if_not_found,
                                screenshot=screenshot, grayscale_mode=grayscale_mode)
    if tl is None:
        return None
    x0, y0 = int(round(tl[0])), int(round(tl[1]))
    x1, y1 = x0 + w_a, y0 + h_a

    screenshot = take_screenshot(screenshot=screenshot, grayscale_mode=grayscale_mode)
    H, W = screenshot.shape[:2]

    # Perpendicular span required to fit template_b next to template_a
    needed_perp = h_b if direction in ('left', 'right') else w_b

    crop_bounds = _compute_crop_excluding_template_a(x0, y0, w_a, h_a,
                                                     direction, needed_perp, W, H)
    if crop_bounds is None:
        return _handle_not_found(f"[ERROR] Invalid crop for direction '{direction}' "
                                 f"(cannot exclude template_a and expand).",
                                 exception_if_not_found, warn_if_not_found)

    crop_x0, crop_y0, crop_x1, crop_y1 = crop_bounds
    crop_gray = screenshot[crop_y0:crop_y1, crop_x0:crop_x1]
    ch, cw = crop_gray.shape[:2]

    if h_b > ch or w_b > cw:
        return _handle_not_found(f"[ERROR] template_b ({w_b}x{h_b}) larger than crop "
                                 f"({cw}x{ch}) after adjustment.",
                                 exception_if_not_found, warn_if_not_found)

    result = cv2.matchTemplate(crop_gray, template_b, cv2.TM_CCOEFF_NORMED)
    ys, xs = np.where(result >= minimal_confidence)

    if len(xs) == 0:
        return _handle_not_found(f"[ERROR] No match for template_b above threshold "
                                 f"{minimal_confidence:.3f} in direction '{direction}' from template_a.",
                                 exception_if_not_found, warn_if_not_found)

    # Choose closest along direction (ties: perpendicular proximity, then higher score)
    candidates = []
    for yy, xx in zip(ys, xs):
        cand_x = crop_x0 + int(xx)  # top-left in screen coords
        cand_y = crop_y0 + int(yy)

        if direction == 'right':
            primary = cand_x - x1
            secondary = abs(cand_y - y0)
        elif direction == 'left':
            primary = x0 - (cand_x + w_b)
            secondary = abs(cand_y - y0)
        elif direction == 'down':
            primary = cand_y - y1
            secondary = abs(cand_x - x0)
        else:  # 'up'
            primary = y0 - (cand_y + h_b)
            secondary = abs(cand_x - x0)

        if primary < 0:  # should not happen since crop excludes A, but keep guard
            continue

        score = float(result[yy, xx])
        candidates.append(((primary, secondary, -score), (cand_x, cand_y)))

    if not candidates:
        return _handle_not_found(f"[ERROR] Matches found, but none lie in the "
                                 f"'{direction}' direction from template_a.",
                                 exception_if_not_found, warn_if_not_found)

    candidates.sort(key=lambda t: t[0])
    best_x, best_y = candidates[0][1]

    return get_relative_point_position(best_x, best_y, w_b, h_b, relative_position)


def paste_value(value: Optional[str], location=None, click=True, delete_existing=True):
    """Paste a value at a screen location via the clipboard, restoring the previous clipboard content."""
    if value is None:
        return
    if click and location is not None:
        pyautogui.click(location)  # Click to focus on the field
    if delete_existing:
        pyautogui.hotkey("ctrl", "a")  # Select any existing text
        pyautogui.press("backspace")  # Clear the field
    original_clipboard = pyperclip.paste()
    pyperclip.copy(str(value))
    sleep(0.05)  # Give some time for the clipboard to update
    pyautogui.hotkey('ctrl', 'v')
    sleep(0.3)  # Let the target app read the clipboard before restoring it
    pyperclip.copy(original_clipboard)


def record_gui_template(template_name: str | None = None, show_results: bool = True):
    """
    Record a GUI template by capturing a screen region and computing its position.
    Steps:
        1. Wait for the user to confirm the target patch is visible, then screenshot.
        2. Get bounding box corners from the user.
        3. Crop and save the template image.
        4. Record target position (as a relative_position) if the user marks one.

    Known limitation: ImageGrab.grab() captures the primary monitor only, while
    cursor coordinates span the whole virtual desktop - record on the primary monitor.
    """
    if get_cursor_position("Make sure the target screen patch is visible and press Left Ctrl to continue.") is None:
        return

    screenshot = np.array(ImageGrab.grab())
    screenshot_height, screenshot_width = screenshot.shape[0], screenshot.shape[1]

    ll_screen = get_cursor_position("Place the cursor on the LOWER LEFT corner of the box and press Left Ctrl.")
    ur_screen = get_cursor_position("Place the cursor on the UPPER RIGHT corner of the box and press Left Ctrl.")
    if ll_screen is None or ur_screen is None:
        print("[ERROR] Bounding box not recorded, aborting.")
        return

    x1, y1 = ll_screen[0], ll_screen[1]
    x2, y2 = ur_screen[0], ur_screen[1]

    left, right = min(x1, x2), max(x1, x2)
    top, bottom = min(y1, y2), max(y1, y2)
    width = right - left
    height = bottom - top

    if width <= 0 or height <= 0:
        print(f"[ERROR] Invalid bounding box dimensions: width={width}, height={height}")
        return

    cropped = screenshot[top:bottom, left:right]
    if show_results:
        from matplotlib import use
        use('tkagg')
        import matplotlib.pyplot as plt
        print(f"{left=}, {top=}, {right=}, {bottom=}, {width=}, {height=}")
        plt.imshow(cropped)
        plt.show()

    target_point = get_cursor_position("Place the cursor at the TARGET DESTINATION and press Left Ctrl.")
    if target_point is not None:
        tx, ty = target_point[0], target_point[1]
        # Relative to the box's bottom-left corner, y-axis pointing up
        # (the convention of get_relative_point_position)
        relative_x = (tx - left) / width
        relative_y = (bottom - ty) / height
    else:
        relative_x, relative_y = None, None

    if template_name is None:
        template_name = input("Enter a name for the template (without extension), then press Enter: ").strip()
    if template_name.endswith('.png'):
        template_name = template_name[:-4]
    os.makedirs(GENERAL_GUI_CONTROLLER_TEMPLATES_PATH, exist_ok=True)
    output_path = os.path.join(GENERAL_GUI_CONTROLLER_TEMPLATES_PATH,
                               f"{template_name} - {screenshot_width}X{screenshot_height}.png")
    cv2.imwrite(output_path, cv2.cvtColor(cropped, cv2.COLOR_RGB2BGR))
    print(f"Saved cropped image to: {output_path}")

    if relative_x is None or relative_y is None:
        templates_usage_syntax = f'detect_template_and_act(r"{template_name}")'
    else:
        templates_usage_syntax = (f'detect_template_and_act(r"{template_name}", '
                                  f'relative_position=({relative_x:.3f}, {relative_y:.3f}))')
    pyperclip.copy(templates_usage_syntax)
    print(templates_usage_syntax)
