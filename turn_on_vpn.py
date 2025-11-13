from core.general_gui_controller import *
from matplotlib import use
use('TkAgg')
# %%
# record_gui_template(template_name='vpn - wisotp - message')

# %%
pyautogui.FAILSAFE = False

edge_icon_location = detect_template_and_act('vpn - edge icon', click=True, sleep_after_action=0.5)
pyautogui.hotkey('alt', 'd')
pyautogui.write(r"https://evpn.weizmann.ac.il/my.policy")
sleep(1)
pyautogui.press('enter')

detect_template_and_act('vpn - click here button', click=True, sleep_after_action=1, max_waiting_time_seconds=3)
pyautogui.press('enter')

detect_template_and_act('vpn - chrome icon', click=True, sleep_after_action=0.5)
detect_template(r"chrome - chrome is opened")
pyautogui.hotkey('ctrl', 't')
sleep(0.1)
detect_template_and_act(['vpn - messages icon', 'vpn - messages icon - gray'], click=True, sleep_after_action=0.5, minimal_confidence=0.999)
# %%
detect_template_and_act(['vpn - wisotp - chat'], click=True, sleep_after_action=0.5, minimal_confidence=0.999)

# otp_location = detect_template_and_act(r"vpn - wisotp message", relative_position=(1.2, 0.5), click=False,
#                                        multiple_matches_sorter=np.array([0.2, -1]))
otp_location = detect_template_and_act(r"vpn - wisotp - message", relative_position=(1.281, 0.615), multiple_matches_sorter=np.array([0.2, -1]), click=False)
pyautogui.doubleClick(otp_location)
pyautogui.hotkey('ctrl', 'c')
# %%
# Alt tab tack to edge:
detect_template_and_act(click=True, sleep_after_action=1,
                        override_coordinates=edge_icon_location)  # , override_coordinates=edge_icon_location
pyautogui.hotkey('ctrl', 'v')
pyautogui.press('enter')

detect_template_and_act(r"vpn - Start button", click=True)

