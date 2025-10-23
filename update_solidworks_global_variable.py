from core.general_gui_controller import *

equations_path = r"C:\Users\michaeka\Weizmann Institute Dropbox\Michael Kali\Labs Dropbox\Laser Phase Plate\Designs\Optomechanics\Parts\equations.txt"
SHORT_SLEEP = 0.1
# %%
# record_gui_template('solidworks - solidworks link to external file marked checkbox - 2560-1440')

# %%
detect_template_and_act(r"solidworks - search bar", relative_position=(1.386, 0.674), value_to_paste='eq', sleep_after_action=SHORT_SLEEP)

detect_template_and_act(r"solidworks - equations", sleep_after_action=SHORT_SLEEP)

detect_template(r"solidworks - angular units label")

three_dots_position = detect_template_and_act(r"solidworks - open file three dots", relative_position=(0.233, 0.388), sleep_after_action=SHORT_SLEEP, max_waiting_time_seconds=0.5)

if three_dots_position is None:
    detect_template_and_act(r"solidworks - link to external file checkbox", relative_position=(0.405, 0.579))

detect_template_and_act(r"solidworks - second open file three dots", relative_position=(0.508, 0.160))

detect_template(r"solidworks - solidworks equations file type")

sleep(SHORT_SLEEP)
pyautogui.write(equations_path)
sleep(SHORT_SLEEP)
pyautogui.press('enter')
sleep(SHORT_SLEEP)

detect_template_and_act(r"solidworks - link button", relative_position=(0.548, 0.592), sleep_after_action=SHORT_SLEEP)

wait_for_template_to_disappear("solidworks - link button")

checkbox_position = detect_template_and_act(r"solidworks - solidworks link to external file marked checkbox - 2560-1440.png", relative_position=(0.092, 0.474))

sleep(3)

pyautogui.click(checkbox_position)

sleep(3)

detect_template_and_act(r"solidworks - link button", relative_position=(0.548, 0.592), sleep_after_action=SHORT_SLEEP)

wait_for_template_to_disappear("solidworks - link button")

# detect_template_and_act(r"solidworks - ok button", relative_position=(0.461, 0.745))