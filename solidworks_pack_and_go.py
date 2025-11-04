from core.general_gui_controller import *
import os

DESTINATION_FOLDER = r"C:\Users\michaeka\Weizmann Institute Dropbox\Michael Kali\Labs Dropbox\Laser Phase Plate\Designs\Optomechanics\Standalone files"
SHORT_SLEEP_TIME = 0.1
# %%
# template_name = 'Save all'
# record_gui_template(file_name=f'Solidworks - {template_name} - 2560X1440')

# %%

detect_template_and_act(r"Solidworks - Filse - 2560X1440", sleep_after_action=SHORT_SLEEP_TIME)

detect_template_and_act(r"Solidworks - Pack and go - 2560X1440", sleep_after_action=SHORT_SLEEP_TIME)
# %%
detect_template_and_act(r"Solidworks - Browse - 2560X1440", sleep_after_action=SHORT_SLEEP_TIME)

pyautogui.hotkey('alt', 'd')

pyautogui.write(DESTINATION_FOLDER)

pyautogui.press('enter')

detect_template_and_act(r"Solidworks - Select Folder - 2560X1440", sleep_after_action=SHORT_SLEEP_TIME)
# %%
detect_template_and_act(r"Solidworks - Save - 2560X1440", sleep_after_action=SHORT_SLEEP_TIME)

detect_template_and_act(r"Solidworks - Confirm replace files - 2560X1440", relative_position=(0.346, 0.375),
                        max_waiting_time_seconds=2, sleep_after_action=SHORT_SLEEP_TIME)

detect_template_and_act(r"Solidworks - Confirm replace files - 2560X1440", relative_position=(0.346, 0.375),
                        max_waiting_time_seconds=2, sleep_after_action=SHORT_SLEEP_TIME)

wait_for_template_to_disappear('Solidworks - save cancel help - 2560X1440')
# %%
sleep(2)
pyautogui.hotkey('ctrl', 'w')

detect_template_and_act(r"Solidworks - Save all, dont save, cancel help - 2560X1440",
                        relative_position=(0.139, 0.387),
                        sleep_after_action=SHORT_SLEEP_TIME,
                        max_waiting_time_seconds=2)
# %%
detect_template_and_act(r"Solidworks - Save all, dont save, cancel help - 2560X1440",
                        relative_position=(0.139, 0.387),
                        sleep_after_action=SHORT_SLEEP_TIME,
                        max_waiting_time_seconds=2)
# %%
detect_template_and_act(r"Solidworks - Save all - 2560X1440", sleep_after_action=SHORT_SLEEP_TIME, max_waiting_time_seconds=2)

detect_template_and_act(r"Solidworks - Save all - 2560X1440", sleep_after_action=SHORT_SLEEP_TIME, max_waiting_time_seconds=2)

wait_for_template_to_disappear(r"Solidworks - Insert - 2560X1440")

# %% iterate over all files paths in C:\Users\michaeka\Weizmann Institute Dropbox\Michael Kali\Labs Dropbox\Lab utilities\Drawings (shared with Guy)\LPP Optomechanics+Vacuum\Parts that end with .sldprt:
parts_folder = os.path.join(DESTINATION_FOLDER, 'Parts')
for root, dirs, files in os.walk(parts_folder):
    for file in files:
        if file.lower().endswith(".sldprt"):
            part_path = os.path.join(root, file)
            detect_template_and_act(r"Solidworks - File - 2560X1440", sleep_after_action=SHORT_SLEEP_TIME)
            detect_template_and_act(r"Solidworks - Open - 2560X1440", sleep_after_action=SHORT_SLEEP_TIME)
            detect_template_and_act(r"Solidworks - File name - 2560X1440", relative_position=(2.129, 0.364),
                                    text_to_paste=part_path, sleep_after_action=SHORT_SLEEP_TIME)
            pyautogui.press('enter')
            detect_template(r"Solidworks - Insert - 2560X1440")
            sleep(2)
            detect_template_and_act(r"solidworks - search bar", relative_position=(1.386, 0.674),
                                    sleep_after_action=SHORT_SLEEP_TIME,
                                    text_to_paste='eq')

            detect_template_and_act(r"solidworks - equations", sleep_after_action=SHORT_SLEEP_TIME)

            detect_template(r"solidworks - angular units label")

            checked_checkbox = detect_template_and_act(r"Solidworks - checked link to external file checkbox - 2560X1440", relative_position=(0.304, 0.619), sleep_after_action=SHORT_SLEEP_TIME, max_waiting_time_seconds=1)
            if checked_checkbox is not None:
                wait_for_template_to_disappear(r"Solidworks - many checked links - 2560X1440")

            detect_template_and_act(r"solidworks - ok button", relative_position=(0.461, 0.745), sleep_after_action=SHORT_SLEEP_TIME)

            pyautogui.hotkey('ctrl', 'w')

            detect_template_and_act(r"Solidworks - Save all - 2560X1440", sleep_after_action=SHORT_SLEEP_TIME)

            wait_for_template_to_disappear(r"Solidworks - Insert - 2560X1440")






