import os
import sys

# Go to the parent of the parent directory
current_file_path = os.path.abspath(__file__)
script_dir = os.path.dirname(current_file_path)

# Go to the parent of the parent directory
desired_working_dir = os.path.abspath(os.path.join(script_dir, '..'))

# Set it as the current working directory
os.chdir(desired_working_dir)

# Optional: add it to sys.path if you import other modules from there
if desired_working_dir not in sys.path:
    sys.path.insert(0, desired_working_dir)

from general_gui_controller import *
import pandas as pd
import re
from utils import wait_for_path_from_clipboard
import winsound


# %%
pyautogui.FAILSAFE = False

# Press Ctrl+Shift+A:
edge_icon_location = detect_template_and_act('vpn - edge icon', click=True, sleep_after_action=0.5)
pyautogui.hotkey('alt', 'd')
pyautogui.write(r"https://evpn.weizmann.ac.il/my.policy")
sleep(1)
pyautogui.press('enter')

detect_template_and_act('vpn - click here button', click=True, sleep_after_action=1)
pyautogui.press('enter')

detect_template_and_act('vpn - chrome icon', click=True, sleep_after_action=0.5)
pyautogui.hotkey('ctrl', 't')
sleep(0.1)
detect_template_and_act('vpn - messages icon', click=True, sleep_after_action=0.5)
detect_template_and_act('vpn - WISOTP', click=True, sleep_after_action=0.5)

otp_location = detect_template_and_act(r"vpn - wisotp message",
                                       relative_position=(1.2, 0.5),
                                       multiple_matches_sorter=np.array([0.2, -1]),
                                       click=False)
pyautogui.doubleClick(otp_location)
pyautogui.hotkey('ctrl', 'c')

# Alt tab tack to edge:
detect_template_and_act(input_template='vpn - edge icon', click=True, sleep_after_action=1)  # , override_coordinates=edge_icon_location
pyautogui.hotkey('ctrl', 'v')
pyautogui.press('enter')

detect_template_and_act(r"vpn - Start button", click=True)
detect_template_and_act(r"vpn - vpn icon", sleep_before_detection=0)






