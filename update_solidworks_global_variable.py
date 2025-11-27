from core.general_gui_controller import *

equations_path = r"C:\Users\michaeka\Weizmann Institute Dropbox\Michael Kali\Labs Dropbox\Laser Phase Plate\Designs\Optomechanics\Parts\equations.txt"
SHORT_SLEEP = 0.1
# %%
# record_gui_template('solidworks - invalid parameter warning sign')

# %%
detect_template_and_act(r"solidworks - search bar", relative_position=(0, 0), sleep_after_action=SHORT_SLEEP,
                        text_to_paste='eq')

# detect_template_and_act(r"solidworks - equations", sleep_after_action=SHORT_SLEEP)

pyautogui.hotkey('ctrl', 'shift', 'e')

detect_template(r"solidworks - angular units label")

# three_dots_position = detect_template_and_act(r"solidworks - open file three dots", relative_position=(0.233, 0.388),
#                                               sleep_after_action=SHORT_SLEEP, max_waiting_time_seconds=0.5)

# if three_dots_position is None:
checkbox_position = detect_template_and_act(r"solidworks - link to external file checkbox", relative_position=(-0.089, 0.583))

link_button_position = detect_template(r"solidworks - link button", max_waiting_time_seconds=2)

if link_button_position is None:
    pyautogui.click(checkbox_position)
else:
    detect_template_and_act(r"solidworks - second open file three dots", relative_position=(0.476, 0.517))
    sleep(SHORT_SLEEP)
    detect_template_and_act(r"solidworks - file name", relative_position=(1.602, 0.375), text_to_paste=equations_path)
    sleep(SHORT_SLEEP)
    pyautogui.press('enter')
    sleep(SHORT_SLEEP)
    detect_template_and_act(r"solidworks - link button", relative_position=(0.548, 0.592), sleep_after_action=SHORT_SLEEP)

while True:
    warning_sign = detect_template_and_act(r"solidworks - invalid parameter warning sign", relative_position=(1.533, -0.658), max_waiting_time_seconds=2)
    if warning_sign is None:
        break

wait_for_template_to_disappear("solidworks - link button")
sleep(2)
detect_template_and_act(r"solidworks - link to external file checkbox", relative_position=(-0.089, 0.583), sleep_after_action=1)
detect_template_and_act(r"solidworks - link to external file checkbox", relative_position=(-0.089, 0.583), sleep_after_action=1)
detect_template_and_act(r"solidworks - link button", relative_position=(0.548, 0.592), sleep_after_action=SHORT_SLEEP)
wait_for_template_to_disappear("solidworks - link button")

# detect_template_and_act(r"solidworks - ok button", relative_position=(0.461, 0.745))