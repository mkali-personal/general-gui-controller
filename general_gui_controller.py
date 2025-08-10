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


def get_cursor_position(target_name) -> Optional[Tuple[float, float]]:
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
    print(f"x={x}, y={y}, w={w}, h={h}")
    x0, y0 = x, y + h
    if relative_position:
        dx = w * relative_position[0]
        dy = h * relative_position[1]
        return x0 + dx, y0 - dy
    else:
        return x + w / 2, y + h / 2


def detect_template(
        input_template: str,
        relative_position: Optional[Tuple[float, float]] = None,
        minimal_confidence: float = 0.8,
        exception_if_not_found: bool = False,
) -> tuple[Optional[float], Optional[float]] | None:
    template_path = os.path.join(GENERAL_GUI_CONTROLLER_TEMPLATES_PATH, input_template)
    base_name, ext = os.path.splitext(template_path)
    if ext == "":
        template_path = template_path + '.png'

    template_img = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template_img is None:
        raise FileNotFoundError(
            f"File: {template_path} not found, current working directory: {os.getcwd()} (should be os-lab)")

    screenshot = ImageGrab.grab()
    screenshot = np.array(screenshot)

    template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
    screen_gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)

    best_val = -1
    best_loc = None
    best_w, best_h = 0, 0

    scales = [1.0] + [s for s in np.linspace(0.5, 2.0, 50) if abs(s - 1.0) > 1e-6]
    for scale in scales:
        resized_template = cv2.resize(template_gray, (0, 0), fx=scale, fy=scale)
        tH, tW = resized_template.shape[:2]

        if tH > screen_gray.shape[0] or tW > screen_gray.shape[1]:
            continue

        result = cv2.matchTemplate(screen_gray, resized_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val > best_val:
            best_val = max_val
            best_loc = max_loc
            best_w, best_h = tW, tH
            if best_val > minimal_confidence:
                break

    if best_loc and best_val > minimal_confidence:
        x, y = best_loc
        px, py = get_relative_point_position(x, y, best_w, best_h, relative_position)
        abs_x, abs_y = px, py  # px + crop_offset_x, py + crop_offset_y
        return abs_x, abs_y
    else:
        failure_text = f"[ERROR] Failed to fit template: {template_path}"
        if exception_if_not_found:
            raise RuntimeError(failure_text)
        else:
            warn(failure_text)
            return None


def detect_template_and_act(
        input_template: Optional[str],
        relative_position: Optional[Tuple[float, float]] = None,
        minimal_confidence: float = 0.8,
        exception_if_not_found: bool = False,
        place_cursor: bool = True,
        click: bool = True,
        sleep_before_detection: Optional[float] = None,
        sleep_after_action: Optional[float] = None,
        value_to_past=None,
        override_coordinates: Optional[tuple[float, float]] = None,
) -> tuple[float, float] | None:
    assert value_to_past is None or click is True, "Cannot paste text without clicking the target location first."
    assert input_template is not None or override_coordinates is not None, \
        "Either input_template or override_coordinates must be provided."

    if sleep_before_detection is not None:
        sleep(sleep_before_detection)
    if override_coordinates is None:
        coordinates = detect_template(input_template=input_template,
                                      relative_position=relative_position,
                                      minimal_confidence=minimal_confidence,
                                      exception_if_not_found=exception_if_not_found)
    else:
        coordinates = override_coordinates
    if coordinates is not None:
        if click:
            pyautogui.click(coordinates[0], coordinates[1])
            if value_to_past is not None:
                paste_value(value_to_past, coordinates, click=False, delete_existing=True)
        elif place_cursor:
            pyautogui.moveTo(coordinates[0], coordinates[1])

        if sleep_after_action is not None:
            sleep(sleep_after_action)
    return coordinates


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
    record_gui_template()


