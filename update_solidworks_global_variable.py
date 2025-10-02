from core.general_gui_controller import *

equations_path = r"C:\Users\michaeka\Weizmann Institute Dropbox\Michael Kali\Labs Dropbox\Laser Phase Plate\Designs\Optomechanics\Parts\equations.txt"
SHORT_SLEEP = 0.1
# %%
# record_gui_template('solidworks - second open file three dots - 1920X1200.png')

# %%
detect_template_and_act(r"solidworks - search bar - 1920X1200.png", relative_position=(1.386, 0.674), value_to_paste='eq', sleep_after_action=SHORT_SLEEP)

detect_template_and_act(r"solidworks - equations - 1920X1200.png", sleep_after_action=SHORT_SLEEP)

three_dots_position = detect_template_and_act(r"solidworks - open file three dots - 1920X1200.png", relative_position=(0.233, 0.388), sleep_after_action=SHORT_SLEEP, max_waiting_time_seconds=2)

if three_dots_position is None:
    detect_template_and_act(r"solidworks - link to external file checkbox - 1920X1200.png", relative_position=(0.405, 0.579))

detect_template_and_act(r"solidworks - second open file three dots - 1920X1200.png", relative_position=(0.508, 0.160))
paste_value(equations_path)

pyautogui.press('enter')
sleep(SHORT_SLEEP)

detect_template_and_act(r"solidworks - link file - 1920X1200.png", relative_position=(0.548, 0.592), sleep_after_action=SHORT_SLEEP)

wait_for_template_to_disappear("solidworks - link file - 1920X1200.png")

detect_template_and_act(r"solidworks - ok button - 1920X1200.png", relative_position=(0.461, 0.745))