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
# %%
from utilities.automations.general_gui_controller import *
import pandas as pd
import re
from utilities.media_tools.utils import wait_for_path_from_clipboard
import winsound
from local_config import PATH_DROPBOX

pyautogui.FAILSAFE = False

# %%
def load_tabular_data(path: str) -> pd.DataFrame:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"[ERROR] File does not exist: {path}")

    lower_path = path.lower()

    # Case 1: CSV file
    if lower_path.endswith(".csv"):
        return pd.read_csv(path)

    # Case 2: Excel file
    elif lower_path.endswith((".xlsx", ".xls")):
        xls = pd.ExcelFile(path)
        sheet_names = xls.sheet_names

        if len(sheet_names) == 1:
            return pd.read_excel(xls, sheet_name=0)

        elif len(sheet_names) > 1:
            print("Multiple sheets found:")
            for idx, name in enumerate(sheet_names[:10]):  # Limit to 10
                print(f"{idx}: {name}")

            choice = input("Select a sheet by entering its index (0-9): ").strip()

            if not choice.isdigit() or not (0 <= int(choice) < len(sheet_names[:10])):
                raise ValueError("[ERROR] Invalid sheet selection.")

            return pd.read_excel(xls, sheet_name=int(choice))

    # Unsupported format
    raise ValueError(f"[ERROR] Unsupported file format: {path}")


def clean_number(x):
    if isinstance(x, str):
        # Remove commas before extracting numbers
        x_no_commas = x.replace(',', '')
        match = re.search(r'[\d.]+', x_no_commas)
        x_extracted = float(match.group()) if match else None
        return x_extracted
    elif isinstance(x, (int, float)):
        return x
    else:
        return None


def clean_text(x):
    # Removes '*' from text:
    if isinstance(x, str):
        return x.replace('*', '').strip()
    elif isinstance(x, (int, float)):
        return str(x).strip()
    else:
        return None


def remove_vat(price):
    if isinstance(price, str):
        price = float(price.replace(',', ''))
    return np.ceil(price / 1.18 * 100) / 100 if isinstance(price, (int, float)) else None


def parse_scientific_table(df: pd.DataFrame, rosh_electroptics_format: bool = False, scientific: bool = True) -> pd.DataFrame:
    # Check the file extension and load the file

    if scientific:
        # Define the target columns in lowercase
        required_columns = ['id', 'description', 'quantity', 'price', 'discount']
        if rosh_electroptics_format:
            # remove the last line of the dataframe if it's Ln value is nan:
            if df.iloc[-1]['Quantity'] == 'TOTAL':
                df = df.iloc[:-1]
            df[['id', 'description']] = df['Part Number and Description'].str.split('\n', n=1, expand=True)
            # rename the column "unit price" to "price":
            df.rename(columns={'Unit Price': 'price'}, inplace=True)

        # Normalize column names to lowercase for matching
        df.columns = df.columns.str.lower()

        # Ensure all required columns exist, adding missing columns as empty
        for col in required_columns:
            if col not in df.columns:
                df[col] = None

        # Clean the columns
        # Clean the columns
        df['discount'] = df['discount'].apply(clean_number)
        df['discount'] = df['discount'].apply(lambda x: 0 if x is None else x * 100 if x < 1 else x)
        df['quantity'] = df['quantity'].apply(clean_number)
        df['price'] = df['price'].apply(clean_number)
        df['id'] = df['id'].apply(clean_text)
        df['description'] = df['description'].apply(clean_text)
        df['description'].fillna('.', inplace=True)

        # Select and return only the required columns
        df = df.loc[:df.last_valid_index()]
        return df[required_columns]
    else:
        required_columns = ['description', 'quantity', 'price']

        # Normalize column names to lowercase for matching
        df.columns = df.columns.str.lower()

        # Ensure all required columns exist, adding missing columns as empty
        for col in required_columns:
            if col not in df.columns:
                df[col] = None

        df['price'] = df['price'].apply(remove_vat)
        df['quantity'] = df['quantity'].apply(clean_number)

        return df
#
#
winsound.Beep(880, 500)
input("got to the TAFNIT main window, and make sure it is maximized on your main screen (where the notification is).\n"
      "When you will need to choose supplier or a quote file in Tafnit, the script will wait for you to choose it,\n"
      "and after choosing, you will need to go back here and press enter\n"
      "Whenever you here a beep sound (speakers/earphones need to be connected and on, not muted), come back here and follow the instructions.\n"
      "Press Enter to continue")

winsound.Beep(880, 500)
scientific_or_food_text = input("If this is a scientific purchase, press s, and if it is a food purchase, press f.\n")
if scientific_or_food_text.lower() == 's':
    scientific = True
elif scientific_or_food_text.lower() == 'f':
    scientific = False
else:
    print("Invalid input. Please enter 's' for scientific or 'f' for food.")
    exit()
#

SHORT_SLEEP_TIME = 0.2
MEDIUM_SLEEP_TIME = 1
LONG_SLEEP_TIME = 4


detect_template_and_act('vpn - chrome icon', sleep_after_action=SHORT_SLEEP_TIME)
pyautogui.hotkey('ctrl', 't')

pyautogui.write(r"https://tafnit.weizmann.ac.il/MENU1/LOGINNoD.CSP")
pyautogui.press('enter')

detect_template_and_act(r"tafnit - user_name field.png", relative_position=(0.230, 0.447))
input('kaki')
# %%
# # # %% Main menu navigation::
button_position = detect_template_and_act('ivrit - main', relative_position=(0.5, 0.3), click=True,
                                          sleep_after_action=SHORT_SLEEP_TIME)
button_position = detect_template_and_act('yazam', relative_position=(-0.5, 0.3), click=True,
                                          sleep_after_action=0.5)
button_position = detect_template_and_act('ivrit - secondary', click=True, sleep_after_action=SHORT_SLEEP_TIME)
button_position = detect_template_and_act('klita', click=True)
pyautogui.moveTo(2, 2)
time.sleep(1)

if scientific:
    button_position = detect_template_and_act("drisha lerechesh", click=True, sleep_after_action=10)
else:
    button_position = detect_template_and_act('hazmana kaspit sherutim', click=True)

# Wait for the menu to fully load:
detect_template('ivrit - main', max_waiting_time_seconds=np.inf)


# %% Supplier selection:
button_position = detect_template_and_act('sapak', click=True, sleep_after_action=SHORT_SLEEP_TIME, sleep_before_detection=3)

wait_for_template('tafnit - pirtei sochen.png')

detect_template_and_act(input_template='tafnit - sochen',
                        secondary_template='tafnit - open window button',
                        secondary_template_direction='right'),

wait_for_template('tafnit - external window toolbar')

winsound.Beep(880, 500)
continue_keyword = input(
    "Choose the supplier from the list, go back here, and press enter to continue or s to stop and exit\n")
if continue_keyword.lower() == 'e':
    exit()


# %% Upload quote:
nispachim_position = detect_template_and_act('nispachim', click=True, sleep_after_action=SHORT_SLEEP_TIME)
sherutei_archive_position = detect_template_and_act('sherutei archive', click=True,
                                                    sleep_after_action=MEDIUM_SLEEP_TIME)
teur_mismach_position = detect_template_and_act('teur mismach', relative_position=(0.1, 0.5), click=True,
                                                sleep_after_action=SHORT_SLEEP_TIME, value_to_paste='quote')
haalaa_lasharat_position = detect_template_and_act('haalaa lasharat', click=True)
bechar_kovets_position = detect_template_and_act('bechar kovets', click=True)
winsound.Beep(880, 500)
ask_continue = False
if scientific is False:
    repetitive_food_order = input("Do you want to use the repetitive food orders excel? (y/n)")
    repetitive_food_order = repetitive_food_order.lower()
    if repetitive_food_order:
        quote_path = os.path.join(PATH_DROPBOX, r"Lab utilities\recurrent food order.xlsx")
        paste_value(quote_path)
        sleep(SHORT_SLEEP_TIME)
        pyautogui.press('enter')
    else:
        ask_continue = True
else:
    ask_continue = True
if ask_continue:
    continue_keyword = input(
        "Choose the quote from the list, go back here, and press enter to continue or s to stop and exit\n")
    if continue_keyword.lower() == 'e':
        exit()

ishur_upload_position = detect_template_and_act('ishur - upload', relative_position=(0.8, 0.5),
                                                minimal_confidence=0.97, click=True, wait_for_template_to_appear=False)
# %% Add Note
sleep(3)
detect_template_and_act('hearot', click=True, sleep_after_action=SHORT_SLEEP_TIME)

if scientific:
    detect_template_and_act('weight estimation', click=True, sleep_after_action=SHORT_SLEEP_TIME, value_to_paste='30cmX30cmX30cm  5kg', relative_position=(-0.5, 0.5))
    winsound.Beep(880, 500)
    input("Put the actual dimensions, then come back here and press enter to continue")
    pritim_position = detect_template_and_act('pritim', click=True, sleep_after_action=MEDIUM_SLEEP_TIME)

else:
    notes_position = detect_template_and_act(input_template='hearot nosafot',
                            secondary_template='tafnit - field right edge',
                            secondary_template_direction='left',
                            click=True,
                            sleep_after_action=SHORT_SLEEP_TIME,
                            value_to_paste='נשמח להזמנה 26/08/2025-ל בשעה 12:30. שם איש קשר - מיכאל קלי. טלפון - 0545952783. מכון ויצמן, בניין פיזיקה, כניסה ראשית.')
    winsound.Beep(880, 500)
    input("Put the actual date and contact details, then come back here and press enter to continue")
    pyautogui.click(notes_position)
    sleep(3)
    pyautogui.hotkey('ctrl', 'a')
    sleep(3)
    pyautogui.hotkey('ctrl', 'c')
    sleep(3)
    pritim_position = detect_template_and_act('pritim', click=True, sleep_after_action=MEDIUM_SLEEP_TIME)
    sleep(3)
    detect_template_and_act(input_template='pritim - hearot',
                            secondary_template='tafnit - field right edge',
                            secondary_template_direction='left',
                            click=True,
                            sleep_after_action=SHORT_SLEEP_TIME)
    sleep(3)
    pyautogui.hotkey('ctrl', 'v')
    sleep(3)
winsound.Beep(880, 500)

# %%

category_1_position = detect_template_and_act('categories', relative_position=(-0.4, 0.85), click=True,
                                              sleep_after_action=SHORT_SLEEP_TIME)
if scientific:
    category_1_choice_position = detect_template_and_act('scientific equipment', relative_position=(0.5, 0.5),
                                                         click=True, sleep_after_action=SHORT_SLEEP_TIME)
else:
    category_1_choice_position = detect_template_and_act('sherutim', relative_position=(0.9, 0.5), click=True,
                                                         sleep_after_action=SHORT_SLEEP_TIME)

category_2_position = detect_template_and_act('categories', relative_position=(-0.4, 0.65), click=True,
                                              sleep_after_action=SHORT_SLEEP_TIME)
if scientific:
    category_2_choice_position = detect_template_and_act('laboratory instruments', relative_position=(0.5, 0.5),
                                                         click=True, sleep_after_action=SHORT_SLEEP_TIME)
else:
    category_2_choice_position = detect_template_and_act('eruim kibud achzaka', click=True,
                                                         sleep_after_action=SHORT_SLEEP_TIME)
if not scientific:
    category_3_position = detect_template_and_act('categories', relative_position=(-0.4, 0.35), click=True,
                                                  sleep_after_action=SHORT_SLEEP_TIME)

    category_3_choice_position = detect_template_and_act('kibud kal', click=True,
                                                         sleep_after_action=SHORT_SLEEP_TIME)


# %%

def paste_row_to_fields(row):
    """Pastes values from a DataFrame row into designated screen fields."""

    teur_position = detect_template('teur', relative_position=(-1, 0.5))

    kamut_position = detect_template('kamut', relative_position=(-1, 0.5))

    mechir_bematbea_position = detect_template('mechir bematbea', relative_position=(-1, 0.5))

    print(row)
    pyautogui.click(teur_position)
    sleep(SHORT_SLEEP_TIME)
    pyautogui.click(teur_position)
    sleep(SHORT_SLEEP_TIME)
    paste_value(row['description'], teur_position)
    sleep(SHORT_SLEEP_TIME)
    paste_value(row['quantity'], kamut_position)
    sleep(SHORT_SLEEP_TIME)
    paste_value(row['price'], mechir_bematbea_position)

    if scientific:
        detect_template_and_act('makat_sapak', relative_position=(-0.945, 0.542), value_to_paste=row['id'], sleep_after_action=SHORT_SLEEP_TIME)
        detect_template_and_act('hanacha', relative_position=(-0.5, 0.5), value_to_paste=row['discount'], sleep_after_action=SHORT_SLEEP_TIME)
        pyautogui.click(category_1_position)
        sleep(SHORT_SLEEP_TIME)
        pyautogui.click(category_1_choice_position)
        sleep(SHORT_SLEEP_TIME)
        pyautogui.click(category_2_position)
        sleep(SHORT_SLEEP_TIME)
        pyautogui.click(category_2_choice_position)
        sleep(SHORT_SLEEP_TIME)
        detect_template_and_act('adken shura', click=True)
    else:
        pyautogui.click(category_1_position)
        sleep(SHORT_SLEEP_TIME)
        pyautogui.click(category_1_choice_position)
        sleep(SHORT_SLEEP_TIME)
        pyautogui.click(category_2_position)
        sleep(SHORT_SLEEP_TIME)
        pyautogui.click(category_2_choice_position)
        sleep(SHORT_SLEEP_TIME)
        pyautogui.click(category_3_position)
        sleep(SHORT_SLEEP_TIME)
        pyautogui.click(category_3_choice_position)
        sleep(SHORT_SLEEP_TIME)
        detect_template_and_act('adken shura', click=True)
        sleep(SHORT_SLEEP_TIME)
        pyautogui.press('enter')
        sleep(SHORT_SLEEP_TIME)
    tafnit_warning = detect_template('kalirkosh - OK warning after update row', exception_if_not_found=False,
                                     warn_if_not_found=False, max_waiting_time_seconds=0)
    if tafnit_warning is not None:
        input("there is a problem, fix it and press here enter to continue")
        detect_template_and_act('kalirkosh - OK warning after update row', max_waiting_time_seconds=0,
                        warn_if_not_found=False, exception_if_not_found=False, click=True)


winsound.Beep(880, 500)
rosh_electroptics_format = False
if scientific:
    winsound.Beep(880, 500)
    rosh_electroptics_format = input("Copy the path to the csv containing the items to be ordered to your clipboard.\n"
                            "make sure the file has the following columns: ['id', 'description', 'quantity', 'price', 'discount'] (Capitalization of letters does not matter)\n"
                            "There is no need to remove strings from the values. that is, No need to change '10 %' to 10 and '250.00 USD' to 250.\n"
                            "Notice that in Excel you can choose Data -> Get Data -> From file -> From PDF to automaticall import tables from a PDF file to you excel.\n"
                            "After copying, come back here and press here 'y' if it is Thorlabs format and 'n' if not (without quotes), and then press enter to continue")
    if rosh_electroptics_format.lower() == 'y':
        rosh_electroptics_format = True
    elif rosh_electroptics_format.lower() == 'n':
        rosh_electroptics_format = False
        input(
            )
    else:
        print("Invalid input. Please enter 'y' for Thorlabs format or 'n' for non-Thorlabs format.")
        exit()
else:
    input(
        "Copy the path to the csv containing the items to be ordered to your clipboard. After copying\n"
        "make sure the file has the following columns: ['id', 'description', 'quantity', 'price', 'discount'] (Capitalization of letter does not matter)\n"
        "After copying come back here and press enter to continue")

print('Copy the path to the csv with \n\n')
items_csv = wait_for_path_from_clipboard(filetype='csv')

df = load_tabular_data(items_csv)

if scientific:
    df = parse_scientific_table(df, rosh_electroptics_format=rosh_electroptics_format)
else:
    df.columns = df.columns.str.lower()

for _, sample_row in df.iterrows():
    paste_row_to_fields(sample_row)
    sleep(LONG_SLEEP_TIME)

winsound.Beep(880, 500)
sleep(MEDIUM_SLEEP_TIME)
winsound.Beep(880, 500)
sleep(MEDIUM_SLEEP_TIME)
winsound.Beep(880, 500)
