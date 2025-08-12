# %%
from utilities.automations.general_gui_controller import *
import winsound
import os
from utilities.media_tools.utils import wait_for_path_from_clipboard


# %%
def memorize_locations():
    d = dict()
    d['exposure_time_label'] = detect_template_and_act(r"exposure_time.png", click=True)
    d['exposure_time'] = detect_template_and_act(r"exposure_time.png", relative_position=(2.5, 0.5), click=True,
                                                 sleep_after_action=0.2)
    d['s'] = detect_template('s-ms-mus.png', relative_position=(0.1, -0.5))
    d['ms'] = detect_template('s-ms-mus.png', relative_position=(0.5, -0.5))
    d['mus'] = detect_template('s-ms-mus.png', relative_position=(0.8, -0.5))
    d['ok_cancel_exposure_time'] = detect_template_and_act('ok cancel.png', relative_position=(0.3, 0.5), click=True,
                                                           sleep_after_action=0.2)
    d['gain'] = detect_template_and_act("gain.png", relative_position=(2, 0.5), click=True, sleep_after_action=0.2)
    d['gain_range'] = detect_template("Range 100 5000.png", relative_position=(0.5, -0.3))
    d['ok_cancel_gain'] = detect_template_and_act('ok cancel.png', relative_position=(0.3, 0.5), click=True,
                                                  sleep_after_action=0.2)
    return d


def decompose_exposure_time(exposure_time_ms: float):
    total_us = int(round(exposure_time_ms * 1000))
    seconds = total_us // 1_000_000
    remaining_us = total_us % 1_000_000
    milliseconds = remaining_us // 1000
    microseconds = remaining_us % 1000 if remaining_us is not None else None
    return seconds, milliseconds, microseconds


def insert_exposure_time(s=5, ms=0, mus=None, locations_dict: Optional[dict] = None):
    if locations_dict is None:
        locations_dict = dict()
    detect_template_and_act(r"exposure_time.png", click=True,
                            override_coordinates=locations_dict.get('exposure_time_label'))
    detect_template_and_act(r"exposure_time.png", relative_position=(2.5, 0.5), click=True, sleep_after_action=0.2,
                            override_coordinates=locations_dict.get('exposure_time'))

    detect_template_and_act('s-ms-mus.png', relative_position=(0.1, -0.5), click=True, value_to_past=s,
                            override_coordinates=locations_dict.get('s'))

    detect_template_and_act('s-ms-mus.png', relative_position=(0.5, -0.5), click=True, value_to_past=ms,
                            override_coordinates=locations_dict.get('ms'))
    if mus is not None:
        detect_template_and_act('s-ms-mus.png', relative_position=(0.8, -0.5), click=True, value_to_past=mus,
                                override_coordinates=locations_dict.get('mus'))
    detect_template_and_act('ok cancel.png', relative_position=(0.3, 0.5), click=True, sleep_after_action=0.4,
                            override_coordinates=locations_dict.get('ok_cancel_exposure_time'))


def insert_gain(gain=400, locations_dict: Optional[dict] = None):
    if locations_dict is None:
        locations_dict = dict()
    detect_template_and_act("gain.png", relative_position=(2, 0.5), click=True, sleep_after_action=0.2,
                            override_coordinates=locations_dict.get('gain'))
    detect_template_and_act("Range 100 5000.png", relative_position=(0.5, -0.3), click=True, value_to_past=gain,
                            override_coordinates=locations_dict.get('gain_range'))
    detect_template_and_act('ok cancel.png', relative_position=(0.3, 0.5), click=True, sleep_after_action=0.4,
                            override_coordinates=locations_dict.get('ok_cancel_gain'))


def generate_name_path(session_path, magnification, exposure_time_ms, gain, side):
    if not isinstance(side, str):
        side = f"{side:d}"
    file_name = f"{side} - {magnification:d}x - {exposure_time_ms:d}ms - {gain:d}%.png"
    return os.path.join(session_path, file_name)


def take_an_image(session_path, magnification, exposure_time_ms, gain, side, locations_dict):
    s, ms, mus = decompose_exposure_time(exposure_time_ms)
    insert_exposure_time(0, 100, 0, locations_dict=locations_dict)
    insert_gain(gain, locations_dict=locations_dict)
    insert_exposure_time(s, ms, mus, locations_dict=locations_dict)
    sleep(0.1)
    sleep(exposure_time_ms/1000)
    name_path = generate_name_path(session_path, magnification, exposure_time_ms, gain, side)
    pyautogui.hotkey('ctrl', 's')
    pyperclip.copy(name_path)  # Copy the Hebrew text to the clipboard
    sleep(0.05)  # Give some time for the clipboard to update
    pyautogui.hotkey('ctrl', 'v')
    sleep(1)
    pyperclip.copy(session_path)  # To have it ready for the next call to the function
    pyautogui.hotkey('enter')
    sleep(1)
    detected_warning = detect_template_and_act('overwrite warning.png', relative_position=(0.3, 0.5), click=True)
    if detected_warning is not None:
        winsound.Beep(440, 500)
        raise Exception("overwriting file")


def take_all_images(magnification, side, session_path=None, locations_dict: Optional[dict] = None):
    if session_path is None:
        session_path = wait_for_path_from_clipboard(filetype='dir')

    os.makedirs(session_path, exist_ok=True)

    take_an_image(session_path, magnification, exposure_time_ms=5000, gain=400, side=side, locations_dict=locations_dict)
    take_an_image(session_path, magnification, exposure_time_ms=5000, gain=3000, side=side,
                  locations_dict=locations_dict)
    insert_exposure_time(2, 0, 0, locations_dict=locations_dict)
    insert_gain(5000, locations_dict=locations_dict)
    winsound.Beep(880, 500)
