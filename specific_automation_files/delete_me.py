import os
import sys

import pyautogui

# Go to the parent of the parent directory
desired_working_dir = r"C:\Users\michaeka\git-projects\os-lab"

# Set it as the current working directory
os.chdir(desired_working_dir)

# Optional: add it to sys.path if you import other modules from there
if desired_working_dir not in sys.path:
    sys.path.insert(0, desired_working_dir)

from utilities.automations.general_gui_controller import *
import pandas as pd
import re
from utilities.media_tools.utils import wait_for_path_from_clipboard
import winsound
# %%
# record_gui_template()
# %%
SHORT_SLEEP_TIME = 0.5
detect_template_and_act('vpn - chrome icon', sleep_after_action=SHORT_SLEEP_TIME)
pyautogui.hotkey('ctrl', 't')
pyautogui.write('https://manage.wix.com/dashboard/e3e48276-49cb-42d0-a822-fc07a1c49081/website-channel/?referralInfo=sidebar')
pyautogui.press('enter')
detect_template_and_act('wix - edit site', sleep_after_action=SHORT_SLEEP_TIME, sleep_before_detection=SHORT_SLEEP_TIME)
detect_template_and_act('wix - hamadlich atsmo', sleep_after_action=SHORT_SLEEP_TIME)
detect_template_and_act('wix - edit file', sleep_after_action=SHORT_SLEEP_TIME)
file_dir_madlyx_position = detect_template_and_act(r"wix - hamadlix - three dots.png", relative_position=(0.799, 0.843), sleep_after_action=SHORT_SLEEP_TIME)
detect_template_and_act(r"wix - move to trash.png", sleep_after_action=SHORT_SLEEP_TIME)
detect_template_and_act(r"wix - Upload Media.png", sleep_after_action=SHORT_SLEEP_TIME)
detect_template_and_act(r"wix - Upload from Computer.png", sleep_after_action=SHORT_SLEEP_TIME)
paste_value(r"H:\My Drive\Madlyx\File Itself\המדליך.pdf")
sleep(SHORT_SLEEP_TIME)
pyautogui.press('enter')
wait_for_template("wix - successful upload")
pyautogui.doubleClick(x=file_dir_madlyx_position[0]-50, y=file_dir_madlyx_position[1]+50)
detect_template_and_act(r"wis - Publish", sleep_after_action=SHORT_SLEEP_TIME)
detect_template_and_act(r"wix - Done", sleep_after_action=SHORT_SLEEP_TIME)
detect_template_and_act(r"wix - Mobile edit", sleep_after_action=SHORT_SLEEP_TIME)
detect_template_and_act(r"wix - mobile file icon", sleep_after_action=SHORT_SLEEP_TIME)
detect_template_and_act(r"wix - set up quick actions", sleep_after_action=SHORT_SLEEP_TIME)
detect_template_and_act(r"wix - mobile hamadlich quick actions", sleep_after_action=SHORT_SLEEP_TIME)
detect_template_and_act(r"wix - mobile three dots", relative_position=(0.913, 0.545), sleep_after_action=SHORT_SLEEP_TIME)
detect_template_and_act(r"wix - mobile set up link", sleep_after_action=SHORT_SLEEP_TIME)
detect_template_and_act(r"wix - mobile choose file.png", sleep_after_action=SHORT_SLEEP_TIME)
pyautogui.doubleClick(x=file_dir_madlyx_position[0]-50, y=file_dir_madlyx_position[1]+50)
detect_template_and_act(r"wix - Done", sleep_after_action=SHORT_SLEEP_TIME)
detect_template_and_act(r"wis - Publish", sleep_after_action=SHORT_SLEEP_TIME)