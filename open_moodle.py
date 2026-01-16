from core.general_gui_controller import *
from local_config import TAFNIT_PASSWORD, TAFNIT_USER_NAME
SHORT_SLEEP = 0.1
# record_gui_template(r"wsos - login logo")

# %%
detect_template_and_act('vpn - chrome icon', click=True, sleep_after_action=1)
detect_template(r"chrome - chrome is opened")

# %%
pyautogui.hotkey('ctrl', 't')
sleep(SHORT_SLEEP)
paste_value(r"https://feinberg.weizmann.ac.il/course/view.php?id=1520")
pyautogui.press('enter')

login_button = detect_template_and_act(r"wsos - login button", sleep_before_detection=2, max_waiting_time_seconds=5, sleep_after_action=1)
if login_button is not None:
    detect_template(r"wsos - login logo")
    pyautogui.press('tab')
    paste_value(TAFNIT_USER_NAME)
    pyautogui.press('tab')
    paste_value(TAFNIT_PASSWORD)
    pyautogui.press('tab')
    pyautogui.press('enter')
