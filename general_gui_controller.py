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
from pynput.keyboard import Key, Controller
from plyer import notification

notification.notify(
    title="This is your main screen",
    message="Make sure the GUI you wish to control is visible on this screen.",
    timeout=5
)

# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# import pytesseract

GENERAL_GUI_CONTROLLER_TEMPLATES_PATH = r"utilities\automations\ggc-templates"


def minimize_current_window():
    keyboard = Controller()
    keyboard.press(Key.cmd)  # Windows key
    keyboard.press(Key.down)  # Down arrow
    time.sleep(0.05)
    keyboard.release(Key.down)
    keyboard.release(Key.cmd)
    time.sleep(0.2)  # Small pause between the two presses


def get_cursor_position(target_name):
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


def detect_template_and_act(
        input_template: str,
        relative_position: Optional[Tuple[float, float]] = None,
        minimal_confidence: float = 0.8,
        exception_if_not_found: bool = False,
        place_cursor: bool = True,
        click: bool = True,
        sleep_before_action: Optional[float] = None,
        sleep_after_action: Optional[float] = None,
        paste_text: Optional[str] = None,
        # crop_ll: Optional[Tuple[int, int]] = None,
        # crop_ur: Optional[Tuple[int, int]] = None,
) -> tuple[float, float] | None:
    """
    Detect the position of a text or image template on the screen(s).

    Args:
        input_template (str): File under templates/ (.txt or image), or raw name for text search.
        relative_position (Optional[Tuple[float, float]]): (x%, y%) offset from bottom-left of matched box.

    Returns:
        (x, y): Tuple of floats in global screen coordinates or None if not found.
    """
    assert paste_text is None or click is True, "Cannot paste text without clicking the target location first."

    if sleep_before_action is not None:
        sleep(sleep_before_action)

    coordinates = detect_template(input_template=input_template, relative_position=relative_position,
                                  minimal_confidence=minimal_confidence,
                                  exception_if_not_found=exception_if_not_found)
    if coordinates is not None:
        if click:
            pyautogui.click(coordinates[0], coordinates[1])
            if paste_text is not None:
                paste_value(paste_text, coordinates)
        elif place_cursor:
            pyautogui.moveTo(coordinates[0], coordinates[1])

        if sleep_after_action is not None:
            sleep(sleep_after_action)
    return coordinates


def detect_template(
        input_template: str,
        relative_position: Optional[Tuple[float, float]] = None,
        minimal_confidence: float = 0.8,
        exception_if_not_found: bool = False,
        **kwargs,
) -> tuple[Optional[float], Optional[float]] | None:
    """
    Detect the position of a text or image template on the screen(s).

    Args:
        input_template (str): File under templates/ (.txt or image), or raw name for text search.
        relative_position (Optional[Tuple[float, float]]): (x%, y%) offset from bottom-left of matched box.

    Returns:
        (x, y): Tuple of floats in global screen coordinates or None if not found.
    """

    # 1. Determine the type and contents of the template
    template_path = os.path.join(GENERAL_GUI_CONTROLLER_TEMPLATES_PATH, input_template)
    base_name, ext = os.path.splitext(template_path)
    ext = ext.lower()

    if ext == ".txt":
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            target_text = content if content else os.path.splitext(os.path.basename(input_template))[0]
        except FileNotFoundError:
            target_text = os.path.splitext(os.path.basename(input_template))[0]
        ext = ".txt"  # force OCR logic

    elif ext in [".png", ".jpg", ".jpeg", ".bmp"]:
        target_text = None  # Will use image logic

    elif ext == "":  # <-- NEW HANDLING FOR EXTENSION-LESS INPUTS
        target_text = input_template.strip()
        ext = ".txt"  # Treat it as a text search via OCR

    else:
        print(f"[ERROR] Unsupported template type: {ext}")
        return None

    # 2. Capture all monitors
    screenshot = ImageGrab.grab()  # Takes screenshot of primary monitor (or full virtual desktop)
    screenshot = np.array(screenshot)

    # 3. Crop image if needed  # This turned out to be unreliable with two screens.
    # if crop_ll and crop_ur:
    #     x1, y1 = crop_ll
    #     x2, y2 = crop_ur
    #     top = min(y1, y2)
    #     bottom = max(y1, y2)
    #     left = min(x1, x2)
    #     right = max(x1, x2)
    #
    #     screenshot = screenshot[top:bottom, left:right]
    #     crop_offset_x, crop_offset_y = left, top
    # else:
    #     crop_offset_x, crop_offset_y = 0, 0

    # 4. Template Matching Logic
    # if ext == ".txt":
    #     data = pytesseract.image_to_data(screen_rgb, output_type=pytesseract.Output.DICT, **kwargs)
    #
    #     for i, text in enumerate(data['text']):
    #         if text.strip().lower() == target_text.lower():
    #             x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
    #             px, py = compute_point(x, y, w, h)
    #             abs_x, abs_y = px + crop_offset_x, py + crop_offset_y
    #             print(f"[INFO] Found text '{target_text}' at ({abs_x:.1f}, {abs_y:.1f})")
    #             pyautogui.moveTo(abs_x, abs_y)
    #             if click:
    #                 pyautogui.click(abs_x, abs_y)
    #             if sleep is not None:
    #                 time.sleep(sleep)
    #             return (abs_x, abs_y)
    #
    #     print(f"[WARNING] Text '{target_text}' not found.")
    #     return None

    if ext in [".png", ".jpg", ".jpeg", ".bmp"]:
        template_img = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template_img is None:
            raise FileNotFoundError(
                f"[ERROR] Failed to load image template: {template_path}, current working directory: {os.getcwd()}")

        template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
        screen_gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)

        best_val = -1
        best_loc = None
        best_w, best_h = 0, 0

        scales = [1.0] + [s for s in np.linspace(0.5, 2.0, 20) if abs(s - 1.0) > 1e-6]
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

    else:
        raise ValueError(f"[ERROR] Unsupported template type: {ext}")


def paste_value(value, location):
    """Pastes a given value at a specified screen location."""
    # Copy the value to clipboard
    if value is None:
        return
    pyautogui.click(location)  # Click to focus on the field
    pyautogui.hotkey("ctrl", "a")  # Select any existing text
    pyautogui.hotkey("backspace")  # Clear the field
    pyperclip.copy(str(value))  # Copy the Hebrew text to the clipboard
    pyautogui.hotkey('ctrl', 'v')
    sleep(0.1)


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
        templates_usage_syntax = f'detect_position(r"{filename}.png", sleep=0, click=True)'
    else:
        templates_usage_syntax = f'detect_position(r"{filename}.png", relative_position=({relative_x:.3f}, {relative_y:.3f}), sleep=0, click=True)'
    pyperclip.copy(templates_usage_syntax)
    print(templates_usage_syntax)


if __name__ == "__main__":
    record_gui_template()

# %%
# input("You will now be prompted to choose a csv\excel file for the quote details.\n"
#       "make sure the file has the following columns: ['id', 'description', 'quantity', 'price', 'discount'] (Capitalization of letter does not matter)\n"
#       "There is no need to remove strings from the values. that is, No need to change '10 %' to 10 and '250.00 USD' to 250.\n"
#       "Notice that in Excel you can choose Data -> Get Data -> From file -> From PDF to automaticall import tables from a PDF file to you excel.\n"
#       "Press Enter to continue")
# thorlabs_format = input("Is the quote in Thorlabs format? (Y/N) and press Enter to continue")
# if thorlabs_format.lower() == 'y':
#     thorlabs_format = True
# elif thorlabs_format.lower() == 'n':
#     thorlabs_format = False
#
# df = load_and_select_columns(thorlabs_format=thorlabs_format)
