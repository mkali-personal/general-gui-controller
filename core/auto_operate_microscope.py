# %%
from core.general_gui_controller import *
import winsound
import os
from core.utils import wait_for_path_from_clipboard
import keyboard


def memorize_locations():
    """
    Detect and store the locations of relevant UI elements for microscope automation.
    Returns:
        dict: Mapping of element names to their detected locations.
    """
    locations = dict()
    locations['exposure_time_label'] = detect_template_and_act(r"exposure_time.png", click=True)
    locations['exposure_time'] = detect_template_and_act(r"exposure_time.png", relative_position=(2.5, 0.5), click=True,
                                                         sleep_after_action=0.2)
    locations['s'] = detect_template('s-ms-mus.png', relative_position=(0.1, -0.5))
    locations['ms'] = detect_template('s-ms-mus.png', relative_position=(0.5, -0.5))
    locations['mus'] = detect_template('s-ms-mus.png', relative_position=(0.8, -0.5))
    locations['ok_cancel_exposure_time'] = detect_template_and_act('ok cancel.png', relative_position=(0.3, 0.5),
                                                                   click=True, sleep_after_action=0.2)
    locations['gain'] = detect_template_and_act("gain.png", relative_position=(2, 0.5), click=True,
                                                sleep_after_action=0.2)
    locations['gain_range'] = detect_template("Range 100 5000.png", relative_position=(0.5, -0.3))
    locations['ok_cancel_gain'] = detect_template_and_act('ok cancel.png', relative_position=(0.3, 0.5), click=True,
                                                          sleep_after_action=0.2)
    return locations


def move_mouse_to_center():
    """Move the mouse cursor to the center of the screen."""
    screen_width, screen_height = pyautogui.size()
    center_x = screen_width // 2
    center_y = screen_height // 2
    pyautogui.moveTo(center_x, center_y)


def zoom_in(value):
    """Zoom in/out by scrolling at the center of the screen while holding Ctrl."""
    move_mouse_to_center()
    pyautogui.keyDown('ctrl')
    pyautogui.scroll(value * 120)
    pyautogui.keyUp('ctrl')


def alt_tab():
    """Simulate Alt+Tab to switch windows."""
    print('Alt Tab1')
    keyboard.press_and_release('alt+tab')
    print('Alt Tab2')


def decompose_exposure_time(exposure_time_ms: float):
    """
    Decompose exposure time in milliseconds to seconds, milliseconds, and microseconds.
    Args:
        exposure_time_ms (float): Exposure time in milliseconds.
    Returns:
        tuple: (seconds, milliseconds, microseconds)
    """
    total_us = int(round(exposure_time_ms * 1000))
    seconds = total_us // 1_000_000
    remaining_us = total_us % 1_000_000
    milliseconds = remaining_us // 1000
    microseconds = remaining_us % 1000 if remaining_us is not None else None
    return seconds, milliseconds, microseconds


def _input_exposure_time_fields(s, ms, mus, locations_dict):
    """Helper to input s, ms, mus fields for exposure time."""
    detect_template_and_act('s-ms-mus.png', relative_position=(0.1, -0.5), click=True, text_to_paste=s,
                            override_coordinates=locations_dict.get('s'))
    detect_template_and_act('s-ms-mus.png', relative_position=(0.5, -0.5), click=True, text_to_paste=ms,
                            override_coordinates=locations_dict.get('ms'))
    if mus is not None:
        detect_template_and_act('s-ms-mus.png', relative_position=(0.8, -0.5), click=True, text_to_paste=mus,
                                override_coordinates=locations_dict.get('mus'))


def insert_exposure_time(s=5, ms=0, mus=None, locations_dict=None):
    """
    Insert exposure time values into the microscope UI.
    Args:
        s (int): Seconds
        ms (int): Milliseconds
        mus (int|None): Microseconds
        locations_dict (dict|None): UI element locations
    """
    if locations_dict is None:
        locations_dict = dict()
    detect_template_and_act(r"exposure_time.png", secondary_template=r"microscope_camera - toolbar border",
                            secondary_template_direction="right", relative_position=(-1, 0.5), click=True,
                            sleep_after_action=0.2, override_coordinates=locations_dict.get('exposure_time'))
    _input_exposure_time_fields(s, ms, mus, locations_dict)
    detect_template_and_act('ok cancel.png', relative_position=(0.3, 0.5), click=True, sleep_after_action=0.4,
                            override_coordinates=locations_dict.get('ok_cancel_exposure_time'))


def insert_gain(gain=400, locations_dict=None):
    """
    Insert gain value into the microscope UI.
    Args:
        gain (int): Gain value
        locations_dict (dict|None): UI element locations
    """
    if locations_dict is None:
        locations_dict = dict()
    detect_template_and_act("gain.png", secondary_template=r"microscope_camera - toolbar border",
                            secondary_template_direction="right", relative_position=(-1, 0.5), click=True,
                            sleep_after_action=0.2, override_coordinates=locations_dict.get('gain'))
    detect_template_and_act("Range 100 5000.png", relative_position=(0.5, -0.3), click=True, text_to_paste=gain,
                            override_coordinates=locations_dict.get('gain_range'))
    detect_template_and_act('ok cancel.png', relative_position=(0.3, 0.5), click=True, sleep_after_action=0.4,
                            override_coordinates=locations_dict.get('ok_cancel_gain'))


def generate_name_path(session_path, magnification, exposure_time_ms, gain, side):
    """
    Generate a file path for saving microscope images.
    Args:
        session_path (str): Directory path
        magnification (int): Magnification value
        exposure_time_ms (int): Exposure time in ms
        gain (int): Gain value
        side (str|int): Side identifier
    Returns:
        str: Full file path
    """
    if not isinstance(side, str):
        side = f"{side:d}"
    file_name = f"{side} - {magnification:d}x - {exposure_time_ms:d}ms - {gain:d}%.png"
    return os.path.join(session_path, file_name)


def _save_image_to_path(name_path, session_path):
    """Helper to save image to the specified path using clipboard and hotkeys."""
    pyautogui.hotkey('ctrl', 's')
    pyperclip.copy(name_path)
    sleep(0.05)
    pyautogui.hotkey('ctrl', 'v')
    sleep(1)
    pyperclip.copy(session_path)
    pyautogui.hotkey('enter')
    sleep(1)


def take_an_image(session_path, magnification, exposure_time_ms, gain, side, locations_dict):
    """
    Automate the process of taking and saving a microscope image.
    Args:
        session_path (str): Directory path
        magnification (int): Magnification value
        exposure_time_ms (int): Exposure time in ms
        gain (int): Gain value
        side (str|int): Side identifier
        locations_dict (dict): UI element locations
    """
    s, ms, mus = decompose_exposure_time(exposure_time_ms)
    insert_exposure_time(0, 100, 0, locations_dict=locations_dict)
    insert_gain(gain, locations_dict=locations_dict)
    insert_exposure_time(s, ms, mus, locations_dict=locations_dict)
    sleep(0.1)
    sleep(exposure_time_ms/1000)
    name_path = generate_name_path(session_path, magnification, exposure_time_ms, gain, side)
    _save_image_to_path(name_path, session_path)
    detected_warning = detect_template_and_act('overwrite warning.png', relative_position=(0.3, 0.5), click=True)
    if detected_warning is not None:
        winsound.Beep(440, 500)
        raise Exception("overwriting file")


def take_all_images(magnification, side, session_path=None, locations_dict: Optional[dict] = None):
    if session_path is None:
        session_path = wait_for_path_from_clipboard(filetype='dir')

    os.makedirs(session_path, exist_ok=True)
    detect_template_and_act(input_template=r"exposure_time.png", click=True,
                            override_coordinates=locations_dict.get('exposure_time_label'))
    # take_an_image(session_path, magnification, exposure_time_ms=5000, gain=400, side=side, locations_dict=locations_dict)
    take_an_image(session_path, magnification, exposure_time_ms=5000, gain=3000, side=side,
                  locations_dict=locations_dict)
    insert_exposure_time(2, 0, 0, locations_dict=locations_dict)
    insert_gain(5000, locations_dict=locations_dict)
    winsound.Beep(880, 500)
