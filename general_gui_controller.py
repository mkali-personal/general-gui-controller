import time
from warnings import warn
import cv2
import pyperclip
import numpy as np
import os
from typing import Optional, Tuple
from PIL import ImageGrab
import pyautogui
from pynput import keyboard
from time import sleep
from plyer import notification

notification.notify(
    title="This is your main screen",
    message="Make sure the GUI you wish to control is visible on this screen.",
    timeout=5
)

GENERAL_GUI_CONTROLLER_TEMPLATES_PATH = r"utilities\automations\ggc-templates"


def minimize_current_window():
    keyboard_controller = keyboard.Controller()
    keyboard_controller.press(keyboard.Key.cmd)  # Windows key
    keyboard_controller.press(keyboard.Key.down)  # Down arrow
    time.sleep(0.05)
    keyboard_controller.release(keyboard.Key.down)
    keyboard_controller.release(keyboard.Key.cmd)


def get_cursor_position(target_name: str) -> Optional[Tuple[float, float]]:
    print(f"Place the cursor over the\n{target_name}\nand press the left 'Ctrl' on the keyboard")

    # Define a variable to store the position
    position = None

    # Function to record the cursor position
    def on_press(key):
        nonlocal position
        if key == keyboard.Key.ctrl_l:
            position = pyautogui.position()
            print(position)
            # Stop the listener after capturing position
            return False

        if key == keyboard.Key.esc:
            position = None
            print('User pressed Escape, exiting without recording position.')
            # Stop the listener after capturing position
            return False

    # Start the keyboard listener and wait until Enter is pressed
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

    print(f"Cursor position recorded for {target_name}: {position}\n")
    return position


def get_relative_point_position(x, y, w, h, relative_position: Optional[Tuple[float, float]] = None):
    x0, y0 = x, y + h
    if relative_position:
        dx = w * relative_position[0]
        dy = h * relative_position[1]
        return x0 + dx, y0 - dy
    else:
        return x + w / 2, y + h / 2


def wait_for_template(input_template: str,
                      sleep_cycle: float = 0,
                      verbose: bool = True,
                      ):
    hold_script = True
    I_DOTS = 0
    print(f"Waiting for template '{input_template}' to appear", end="\r")
    while hold_script:
        button_position = detect_template(input_template,
                                          exception_if_not_found=False,
                                          warn_if_not_found=False,)
        if button_position is not None:
            print(f"Found template: {input_template}")
            hold_script = False
        else:
            if verbose:
                I_DOTS = I_DOTS % 3
                dots = '.' * I_DOTS
                print(f"Waiting for template '{input_template}' to appear{dots}", end="\r")
                I_DOTS += 1
            sleep(sleep_cycle)


def load_template(input_template: str, grayscale_mode: bool = True) -> np.ndarray:
    template_path = os.path.join(GENERAL_GUI_CONTROLLER_TEMPLATES_PATH, input_template)
    base_name, ext = os.path.splitext(template_path)
    if ext == "":
        template_path = template_path + '.png'

    template_img = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template_img is None:
        raise FileNotFoundError(
            f"File: {template_path} not found, current working directory: {os.getcwd()} (should be os-lab)")

    if grayscale_mode:
        template_img = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)

    return template_img


def detect_template(
        input_template: str,
        secondary_template: Optional[str] = None,
        secondary_template_direction: Optional[str] = None,
        relative_position: Optional[Tuple[float, float]] = None,
        minimal_confidence: float = 0.8,
        exception_if_not_found: bool = False,
        warn_if_not_found: bool = True,
        grayscale_mode: bool = True,
        wait_for_template_to_appear: bool = True,
) -> tuple[Optional[float], Optional[float]] | None:
    assert (secondary_template is None and secondary_template_direction is None) or (
                secondary_template is not None and secondary_template_direction is not None), \
        "If secondary_template is provided, secondary_template_direction must also be provided."
    assert exception_if_not_found is False or wait_for_template_to_appear is False, \
        "Cannot wait for template to appear if exception_if_not_found is True."

    if secondary_template is not None and secondary_template_direction is not None:
        coordinates = detect_dual_template(
            template_a=input_template,
            template_b=secondary_template,
            direction=secondary_template_direction,
            relative_position=relative_position,
            minimal_confidence=minimal_confidence,
            exception_if_not_found=exception_if_not_found,
            warn_if_not_found=warn_if_not_found,
            grayscale_mode=grayscale_mode,
            wait_for_template_to_appear=wait_for_template_to_appear
        )
        if coordinates is not None:
            return coordinates
        else:
            return None

    template_img = load_template(input_template, grayscale_mode=grayscale_mode)

    screenshot = ImageGrab.grab()
    screenshot = np.array(screenshot)
    if grayscale_mode:  # 3
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)

    best_val = -1
    best_loc = None
    best_w, best_h = 0, 0

    scales = [1.0] + [s for s in np.linspace(0.5, 2.0, 50) if abs(s - 1.0) > 1e-6]
    for scale in scales:
        resized_template = cv2.resize(template_img, (0, 0), fx=scale, fy=scale)
        tH, tW = resized_template.shape[:2]

        if tH > screenshot.shape[0] or tW > screenshot.shape[1]:
            continue

        result = cv2.matchTemplate(screenshot, resized_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val > best_val:
            best_val = max_val
            best_loc = max_loc
            best_w, best_h = tW, tH
            if best_val > minimal_confidence:
                break

    if best_loc and best_val > minimal_confidence:  # If the template was found:
        x, y = best_loc
        px, py = get_relative_point_position(x, y, best_w, best_h, relative_position)
        abs_x, abs_y = px, py  # px + crop_offset_x, py + crop_offset_y
        return abs_x, abs_y
    else:
        if wait_for_template_to_appear:
            print(f"[INFO] Waiting for template: {input_template} to appear...")
            wait_for_template(input_template=input_template)
            # After waiting is done:
            return detect_template(
                input_template=input_template,
                secondary_template=secondary_template,
                secondary_template_direction=secondary_template_direction,
                relative_position=relative_position,
                minimal_confidence=minimal_confidence,
                exception_if_not_found=exception_if_not_found,
                warn_if_not_found=warn_if_not_found,
                grayscale_mode=grayscale_mode,
                wait_for_template_to_appear=False
                )
        else:
            failure_text = f"[ERROR] Failed to fit template: {input_template}"
            if exception_if_not_found:
                raise RuntimeError(failure_text)
            elif warn_if_not_found:
                warn(failure_text)
                return None


def detect_template_and_act(
        input_template: Optional[str],
        secondary_template: Optional[str] = None,
        secondary_template_direction: Optional[str] = None,
        relative_position: Optional[Tuple[float, float]] = None,
        minimal_confidence: float = 0.8,
        exception_if_not_found: bool = False,
        warn_if_not_found: bool = True,
        place_cursor: bool = True,
        click: bool = True,
        sleep_before_detection: Optional[float] = None,
        sleep_after_action: Optional[float] = None,
        value_to_paste=None,
        override_coordinates: Optional[tuple[float, float]] = None,
        grayscale_mode: bool = True,
        wait_for_template_to_appear: bool = True,
) -> tuple[float, float] | None:

    assert value_to_paste is None or click is True, "Cannot paste text without clicking the target location first."
    assert input_template is not None or override_coordinates is not None, \
        "Either input_template or override_coordinates must be provided."

    if sleep_before_detection is not None:
        sleep(sleep_before_detection)
    if override_coordinates is None:
        coordinates = detect_template(input_template=input_template,
                                      secondary_template=secondary_template,
                                      secondary_template_direction=secondary_template_direction,
                                      relative_position=relative_position,
                                      minimal_confidence=minimal_confidence,
                                      exception_if_not_found=exception_if_not_found,
                                      warn_if_not_found=warn_if_not_found,
                                      grayscale_mode=grayscale_mode,
                                      wait_for_template_to_appear=wait_for_template_to_appear)
    else:
        coordinates = override_coordinates
    if coordinates is not None:
        if click:
            pyautogui.click(coordinates[0], coordinates[1])
            if value_to_paste is not None:
                paste_value(value_to_paste, coordinates, click=False, delete_existing=True)
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
    lo = int(lo); hi = int(hi)
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
        # Try the side(s) that still have capacity
        cap_left = new_lo - 0          # how much more we can move left
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
        y_lo = max(0, y0)
        y_hi = min(H, y1)
        y_lo, y_hi = _expand_interval(y_lo, y_hi, needed_perp, H)
        crop_y0, crop_y1 = y_lo, y_hi

    elif direction == 'left':
        crop_x0 = 0
        crop_x1 = max(min(x0, W), 0)
        y_lo = max(0, y0)
        y_hi = min(H, y1)
        y_lo, y_hi = _expand_interval(y_lo, y_hi, needed_perp, H)
        crop_y0, crop_y1 = y_lo, y_hi

    elif direction == 'down':
        crop_y0 = min(max(y1, 0), H)
        crop_y1 = H
        x_lo = max(0, x0)
        x_hi = min(W, x1)
        x_lo, x_hi = _expand_interval(x_lo, x_hi, needed_perp, W)
        crop_x0, crop_x1 = x_lo, x_hi

    else:  # 'up'
        crop_y0 = 0
        crop_y1 = max(min(y0, H), 0)
        x_lo = max(0, x0)
        x_hi = min(W, x1)
        x_lo, x_hi = _expand_interval(x_lo, x_hi, needed_perp, W)
        crop_x0, crop_x1 = x_lo, x_hi

    # Validate crop
    if crop_x1 - crop_x0 <= 0 or crop_y1 - crop_y0 <= 0:
        return None

    return crop_x0, crop_y0, crop_x1, crop_y1


def detect_dual_template(
        template_a: str,
        template_b: str,
        direction: str,
        **kwargs
) -> tuple[Optional[float], Optional[float]] | None:
    """
    Find template_b in a crop that starts immediately AFTER template_a in `direction`
    (crop EXCLUDES template_a). If the perpendicular span of template_a is too small
    to fit template_b, widen/tallen the crop symmetrically as allowed by the screen
    (and reassign any leftover expansion to the other side when clamped).

    Returns a point inside the found template_b (using kwargs.get('relative_position') if provided,
    otherwise the center), or None on failure (unless exception_if_not_found=True).
    """
    direction = direction.lower()
    assert direction in {'up', 'down', 'left', 'right'}, "direction must be one of: 'up', 'down', 'left', 'right'"

    minimal_confidence = kwargs.get('minimal_confidence', 0.8)
    exception_if_not_found = kwargs.get('exception_if_not_found', False)
    warn_if_not_found = kwargs.get('warn_if_not_found', True)
    relative_position_b = kwargs.get('relative_position', None)
    grayscale_mode = kwargs.get('grayscale_mode', True)

    # Load templates
    template_a_img = load_template(template_a, grayscale_mode=grayscale_mode)
    template_b_img = load_template(template_b, grayscale_mode=grayscale_mode)

    h_a, w_a = template_a_img.shape[:2]
    h_b, w_b = template_b_img.shape[:2]

    # Find template_a top-left once
    tl = detect_template(
        input_template=template_a,
        relative_position=(0.0, 1.0),
        minimal_confidence=minimal_confidence,
        exception_if_not_found=exception_if_not_found,
        warn_if_not_found=warn_if_not_found
    )
    if tl is None:
        return None
    x0, y0 = int(round(tl[0])), int(round(tl[1]))

    x1, y1 = x0 + w_a, y0 + h_a

    # Screenshot (grayscale)
    screenshot = ImageGrab.grab()
    screen_rgb = np.array(screenshot)
    screen_gray = cv2.cvtColor(screen_rgb, cv2.COLOR_RGB2GRAY)
    H, W = screen_gray.shape[:2]

    # Determine perpendicular requirement
    needed_perp = h_b if direction in ('left', 'right') else w_b

    # Compute crop that excludes template_a and is widened/tallened if needed
    crop_bounds = _compute_crop_excluding_template_a(x0, y0, w_a, h_a,
                                                     direction,
                                                     needed_perp,
                                                     W, H)
    if crop_bounds is None:
        msg = f"[ERROR] Invalid crop for direction '{direction}' (cannot exclude template_a and expand)."
        if exception_if_not_found:
            raise RuntimeError(msg)
        if warn_if_not_found:
            warn(msg)
        return None

    crop_x0, crop_y0, crop_x1, crop_y1 = crop_bounds
    crop_gray = screen_gray[crop_y0:crop_y1, crop_x0:crop_x1]
    ch, cw = crop_gray.shape[:2]

    # If even after widening/tallening the perpendicular span, template_b still cannot fit
    if h_b > ch or w_b > cw:
        if warn_if_not_found:
            warn(f"[WARN] template_b ({w_b}x{h_b}) larger than crop ({cw}x{ch}) after adjustment.")
        if exception_if_not_found:
            raise RuntimeError("template_b does not fit in crop after adjustment.")
        return None

    # Match template_b within the crop
    result = cv2.matchTemplate(crop_gray, template_b_img, cv2.TM_CCOEFF_NORMED)
    ys, xs = np.where(result >= minimal_confidence)

    if len(xs) == 0:
        msg = (f"[ERROR] No match for template_b above threshold {minimal_confidence:.3f} "
               f"in direction '{direction}' from template_a.")
        if exception_if_not_found:
            raise RuntimeError(msg)
        if warn_if_not_found:
            warn(msg)
        return None

    # Choose closest along direction (ties: perpendicular proximity, then higher score)
    candidates = []
    for yy, xx in zip(ys, xs):
        cand_x = crop_x0 + int(xx)  # top-left in screen coords
        cand_y = crop_y0 + int(yy)

        if direction == 'right':
            primary = cand_x - x1
            if primary < 0:  # should not happen since crop excludes A, but keep guard
                continue
            secondary = abs(cand_y - y0)
            size_w, size_h = w_b, h_b
        elif direction == 'left':
            primary = x0 - (cand_x + w_b)
            if primary < 0:
                continue
            secondary = abs(cand_y - y0)
            size_w, size_h = w_b, h_b
        elif direction == 'down':
            primary = cand_y - y1
            if primary < 0:
                continue
            secondary = abs(cand_x - x0)
            size_w, size_h = w_b, h_b
        else:  # 'up'
            primary = y0 - (cand_y + h_b)
            if primary < 0:
                continue
            secondary = abs(cand_x - x0)
            size_w, size_h = w_b, h_b

        score = float(result[yy, xx])
        candidates.append(((primary, secondary, -score), (cand_x, cand_y), (size_w, size_h)))

    if not candidates:
        msg = f"[ERROR] Matches found, but none lie in the '{direction}' direction from template_a."
        if exception_if_not_found:
            raise RuntimeError(msg)
        if warn_if_not_found:
            warn(msg)
        return None

    candidates.sort(key=lambda t: t[0])
    best_xy = candidates[0][1]
    size_w, size_h = candidates[0][2]
    best_x, best_y = best_xy

    # Return point inside template_b (respecting relative_position if provided)
    abs_x, abs_y = get_relative_point_position(best_x, best_y, size_w, size_h, relative_position_b)
    return abs_x, abs_y


def paste_value(value: Optional[str], location, click=True, delete_existing=True):
    """Pastes a given value at a specified screen location."""
    # Copy the value to clipboard
    if value is None:
        return
    if click and location is not None:
        pyautogui.click(location)  # Click to focus on the field
    if delete_existing:
        pyautogui.hotkey("ctrl", "a")  # Select any existing text
        pyautogui.hotkey("backspace")  # Clear the field
    original_clipboard = pyperclip.paste()
    pyperclip.copy(str(value))  # Copy the Hebrew text to the clipboard
    sleep(0.05)  # Give some time for the clipboard to update
    pyautogui.hotkey('ctrl', 'v')
    pyperclip.copy(original_clipboard)


def record_gui_template():
    # Step 2: Capture screen and compute coordinate shift
    screenshot = ImageGrab.grab()  # Takes screenshot of primary monitor (or full virtual desktop)
    screenshot = np.array(screenshot)

    # Step 1: Get bounding box corners in screen coords
    ll_screen = get_cursor_position("Place the cursor on the LOWER LEFT corner of the box and press Left Ctrl.")
    ur_screen = get_cursor_position("Place the cursor on the UPPER RIGHT corner of the box and press Left Ctrl.")

    # Convert screen coords to image coords
    x1, y1 = ll_screen[0], ll_screen[1]
    x2, y2 = ur_screen[0], ur_screen[1]

    left = min(x1, x2)
    right = max(x1, x2)
    top = min(y1, y2)
    bottom = max(y1, y2)

    width = right - left
    height = bottom - top

    if width <= 0 or height <= 0:
        print(f"[ERROR] Invalid bounding box dimensions: width={width}, height={height}")
        return

    # Step 3: Crop and save
    cropped = screenshot[top:bottom, left:right]

    # Step 4: Record target position
    target_screen = get_cursor_position("Place the cursor at the TARGET DESTINATION and press Left Ctrl.")
    if target_screen is not None:
        tx, ty = target_screen[0], target_screen[1]
        # Step 5: Compute relative position to bottom-left of cropped box
        relative_x = (tx - left) / width
        relative_y = (bottom - ty) / height  # Inverted Y axis
    else:
        relative_x, relative_y = None, None

    filename = input("Enter a name for the template (without extension), then press Enter: ").strip()
    os.makedirs(GENERAL_GUI_CONTROLLER_TEMPLATES_PATH, exist_ok=True)
    output_path = os.path.join(GENERAL_GUI_CONTROLLER_TEMPLATES_PATH, filename + ".png")
    cv2.imwrite(output_path, cv2.cvtColor(cropped, cv2.COLOR_RGB2BGR))
    print(f"Saved cropped image to: {output_path}")

    if relative_x is None or relative_y is None:
        templates_usage_syntax = f'detect_template_and_act(r"{filename}.png", sleep_before_detection=0, click=True)'
    else:
        templates_usage_syntax = f'detect_template_and_act(r"{filename}.png", relative_position=({relative_x:.3f}, {relative_y:.3f}), sleep_before_detection=0, click=True)'
    pyperclip.copy(templates_usage_syntax)
    print(templates_usage_syntax)


if __name__ == "__main__":
    detect_dual_template(template_a='delete_me_a.png', template_b='delete_me_b.png', direction='right',)


