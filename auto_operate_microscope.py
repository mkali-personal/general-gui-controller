# %%
from utilities.automations.general_gui_controller import *
import winsound
import os

# %%
def decompose_exposure_time(exposure_time_ms: float):
    total_us = int(round(exposure_time_ms * 1000))
    seconds = total_us // 1_000_000
    remaining_us = total_us % 1_000_000
    milliseconds = remaining_us // 1000
    microseconds = remaining_us % 1000
    return seconds, milliseconds, microseconds


def insert_exposure_time(s=5, ms=0, mus=0):
    detect_position(r"exposure_time.png", sleep=0, click=True)
    detect_position(r"exposure_time.png", relative_position=(2.5, 0.5), sleep=0, click=True)

    detect_position('s-ms-mus.png', relative_position=(0.1, -0.5), click=True)
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.write(str(s))

    detect_position('s-ms-mus.png', relative_position=(0.5, -0.5), click=True)
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.write(str(ms))

    detect_position('s-ms-mus.png', relative_position=(0.8, -0.5), click=True)
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.write(str(mus))

    detect_position('ok cancel.png', relative_position=(0.3, 0.5), click=True)


def insert_gain(gain=400):
    detect_position("gain.png", relative_position=(2, 0.5), sleep=0, click=True)
    detect_position("Range 100 5000.png", relative_position=(0.5, -0.3), sleep=0, click=True)
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.write(str(gain))
    detect_position('ok cancel.png', relative_position=(0.3, 0.5), click=True)


def generate_name_path(session_path, magnification, exposure_time_ms, gain, ROC):
    session_path_temp = os.path.join(session_path, str(ROC))
    file_name = f"{magnification:d}x - {exposure_time_ms:d}ms - {gain:d}%.png"
    return os.path.join(session_path_temp, file_name)


def take_an_image(session_path, magnification, exposure_time_ms, gain, ROC):
    s, ms, mus = decompose_exposure_time(exposure_time_ms)
    insert_exposure_time(s, ms, mus)
    sleep(0.3)
    insert_gain(gain)
    sleep(0.3)
    sleep(exposure_time_ms * 2 / 1000)
    name_path = generate_name_path(session_path, magnification, exposure_time_ms, gain, ROC)
    pyautogui.hotkey('ctrl', 's')
    pyautogui.write(name_path)
    sleep(1)
    pyautogui.hotkey('enter')
    sleep(1)
    detected_warning = detect_position('overwrite warning.png', relative_position=(0.3, 0.5), click=True)
    if detected_warning is not None:
        winsound.Beep(445, 500)
        raise Exception("overwriting file")


def take_all_images(magnification, ROC, session_path=None):
    if session_path is None:
        session_path = wait_for_path_from_clipboard(filetype='dir')

    session_path_549 = os.path.join(session_path, '549')
    session_path_2422 = os.path.join(session_path, '2422')

    os.makedirs(session_path, exist_ok=True)
    os.makedirs(session_path_549, exist_ok=True)
    os.makedirs(session_path_2422, exist_ok=True)

    take_an_image(session_path, magnification, exposure_time_ms=5000, gain=400, ROC=ROC)
    take_an_image(session_path, magnification, exposure_time_ms=5000, gain=3000, ROC=ROC)
    insert_exposure_time(1, 0, 0)
    insert_gain(5000)
    winsound.Beep(1000, 500)
