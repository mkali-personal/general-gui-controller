import os
import sys

# Get the directory of the current script
current_file_path = os.path.abspath(__file__)
script_dir = os.path.dirname(current_file_path)

# Go to the parent of the parent directory
desired_working_dir = os.path.abspath(os.path.join(script_dir, '..', '..', '..'))

# Set it as the current working directory
os.chdir(desired_working_dir)

# Optional: add it to sys.path if you import other modules from there
if desired_working_dir not in sys.path:
    sys.path.insert(0, desired_working_dir)

from utilities.automations.auto_operate_microscope import *
from utilities.automations.kalifcode import *
import keyboard


def zoom_in(value):
    # Get screen dimensions
    screen_width, screen_height = pyautogui.size()

    # Move mouse to center
    center_x = screen_width // 2
    center_y = screen_height // 2
    pyautogui.moveTo(center_x, center_y)

    # Press Ctrl
    pyautogui.keyDown('ctrl')

    # Perform 3 scrolls down (zoom out)
    pyautogui.scroll(value * 120)

    # Release Ctrl
    pyautogui.keyUp('ctrl')


def alt_tab(value):
    print('Alt Tab1')
    keyboard.press_and_release('alt+tab'),
    print('Alt Tab2')



callback_map = {'twenty ten': lambda: take_all_images(ROC=2422, magnification=10),
                'twenty twenty': lambda: take_all_images(ROC=2422, magnification=20),
                'five ten': lambda: take_all_images(ROC=549, magnification=10),
                'five twenty': lambda: take_all_images(ROC=549, magnification=20),
                'exposure one': lambda: insert_exposure_time(1, 0, 0),
                'exposure two': lambda: insert_exposure_time(2, 0, 0),
                'exposure to': lambda: insert_exposure_time(2, 0, 0),
                'exposure five': lambda: insert_exposure_time(5, 0, 0),
                'exposure four': lambda: insert_exposure_time(4, 0, 0),
                'exposure three': lambda: insert_exposure_time(3, 0, 0),
                'change window': lambda: alt_tab,
                'zoom in': lambda: zoom_in(3),
                'zoom out': lambda: zoom_in(-3)
                }



start_voice_listener(command_map=callback_map)
# %%


