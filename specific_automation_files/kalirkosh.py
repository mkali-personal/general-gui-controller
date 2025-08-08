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

from utilities.automations.general_gui_controller import *

detect_template_and_act(r"copilot icon.png", relative_position=(0.625, 0.480), click=True)

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


def parse_scientific_table(df: pd.DataFrame, thorlabs_format: bool = False, scientific: bool = True) -> pd.DataFrame:
    # Check the file extension and load the file

    if scientific:
        # Define the target columns in lowercase
        required_columns = ['id', 'description', 'quantity', 'price', 'discount']
        if thorlabs_format:
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



input("got to the TAFNIT main window, and make sure it is maximized.\n"
      "When you will need to choose supplier or a quote file in Tafnit, the script will wait for you to choose it,\n"
      "and after choosing, you will not to go back here and press enter\n"
      "Press Enter to continue")
scientific_or_food_text = input("If this is a scientific purchase, press s, and if it is a food purchase, press f.\n")
if scientific_or_food_text.lower() == 's':
    scientific = True
elif scientific_or_food_text.lower() == 'f':
    scientific = False
else:
    print("Invalid input. Please enter 's' for scientific or 'f' for food.")
    exit()

# BOX_LL = get_cursor_position("lower-left corner of the tafnit window")  # (3, 1072)  #
# BOX_UR = get_cursor_position("upper-right corner of the tafnit window")  # (1916, 4)  #
SLEEP_TIME = 0.2
LONG_SLEEP_TIME = 2
# %% Main menu navigation::
button_position = detect_template_and_act('ivrit - main.png', relative_position=(0.5, 0.3), click=True)

button_position = detect_template_and_act('yazam.png', relative_position=(0.5, 0.3), click=True)

button_position = detect_template_and_act('ivrit - secondary.png', click=True)
button_position = detect_template_and_act('klita.png', click=True)
pyautogui.moveTo(2, 2)
time.sleep(LONG_SLEEP_TIME)

if scientific:
    button_position = detect_template_and_act("drisha lerechesh.png", click=True)
else:
    button_position = detect_template_and_act('hazmana kaspit sherutim.png', click=True)

# %% Supplier selection:
button_position = detect_template_and_act('sapak.png', click=True)

button_position = detect_template_and_act('sochen.png', relative_position=(1.6, 0.5), click=True)

continue_keyword = input("Choose the quote from the list, go back here, and press enter to continue or s to stop and exit\n")
if continue_keyword.lower() == 'e':
    exit()

minimize_current_window()

# %% Upload quote:
nispachim_position = detect_template_and_act('nispachim.png')
pyautogui.click(nispachim_position)
sleep(3)

sherutei_archive_position = detect_template_and_act('sherutei archive.png', click=True)

teur_mismach_position = detect_template_and_act('teur mismach.png', relative_position=(0.1, 0.5), click=True)

pyautogui.write('quote')

haalaa_lasharat_position = detect_template_and_act('haalaa lasharat.png', click=True)


bechar_kovets_position = detect_template_and_act('bechar kovets.png', click=True)
continue_keyword = input("Choose the quote from the list, go back here, and press enter to continue or s to stop and exit\n")
if continue_keyword.lower() == 'e':
    exit()
minimize_current_window()
ishur_upload_position = detect_template_and_act('ishur - upload.png', relative_position=(0.8, 0.5),
                                                minimal_confidence=0.97, click=True)


# %%

pritim_position = detect_template_and_act('pritim.png', click=True)

makat_position = detect_template_and_act('makat_sapak.png', relative_position=(-0.945, 0.542), click=False)

hanacha_position = detect_template_and_act('hanacha.png', relative_position=(-0.822, 0.571), click=False)

teur_position = detect_template_and_act('teur.png', relative_position=(-1, 0.5), click=False)

kamut_position = detect_template_and_act('kamut.png', relative_position=(-1, 0.5), click=False)

mechir_bematbea_position = detect_template_and_act('mechir bematbea.png', relative_position=(-1, 0.5), click=False)

adken_shura_position = detect_template_and_act('adken shura.png', click=False)

# %%

category_1_position = detect_template_and_act('categories.png', relative_position=(-0.4, 0.85), click=True)
if scientific:
    category_1_choice_position = detect_template_and_act('scientific equipment.png', relative_position=(0.5, 0.5),
                                                         click=True)
else:
    category_1_choice_position = detect_template_and_act('sherutim.png', relative_position=(0.9, 0.5), click=True)

category_2_position = detect_template_and_act('categories.png', relative_position=(-0.4, 0.65), click=True)
if scientific:
    category_2_choice_position = detect_template_and_act('laboratory instruments.png', relative_position=(0.5, 0.5),
                                                         click=True)
else:
    category_2_choice_position = detect_template_and_act('eruim kibud achzaka.png', click=True)
if not scientific:
    category_3_position = detect_template_and_act('categories.png', relative_position=(-0.4, 0.35), click=True)

    category_3_choice_position = detect_template_and_act('kibud kal.png', click=True)

# %%

def paste_row_to_fields(row):
    """Pastes values from a DataFrame row into designated screen fields."""
    print(row)
    pyautogui.click(teur_position)
    sleep(0.1)
    pyautogui.click(teur_position)
    sleep(0.1)
    paste_value(row['description'], teur_position)
    sleep(SLEEP_TIME)
    paste_value(row['quantity'], kamut_position)
    sleep(SLEEP_TIME)
    paste_value(row['price'], mechir_bematbea_position)

    if scientific:
        paste_value(row['id'], makat_position)
        sleep(1)
        paste_value(row['discount'], hanacha_position)
        sleep(1)
        pyautogui.click(category_1_position)
        pyautogui.click(category_1_choice_position)
        pyautogui.click(category_2_position)
        pyautogui.click(category_2_choice_position)
        sleep(1)
        pyautogui.click(adken_shura_position)
    else:
        pyautogui.click(category_1_position)
        sleep(SLEEP_TIME)
        pyautogui.click(category_1_choice_position)
        sleep(SLEEP_TIME)
        pyautogui.click(category_2_position)
        sleep(SLEEP_TIME)
        pyautogui.click(category_2_choice_position)
        sleep(SLEEP_TIME)
        pyautogui.click(category_3_position)
        sleep(SLEEP_TIME)
        pyautogui.click(category_3_choice_position)
        sleep(SLEEP_TIME)
        pyautogui.click(adken_shura_position)
        sleep(SLEEP_TIME)
        pyautogui.press('enter')
        sleep(SLEEP_TIME)


thorlabs_format = False
if scientific:
     thorlabs_format = input("You will now be prompted to choose a csv\excel file for the items details.\n"
          "is it specifically in Thorlabs format? (Y/N) and press Enter to continue")
     if thorlabs_format.lower() == 'y':
         thorlabs_format = True
     elif thorlabs_format.lower() == 'n':
         thorlabs_format = False
         input(
             "make sure the file has the following columns: ['id', 'description', 'quantity', 'price', 'discount'] (Capitalization of letter does not matter)\n"
             "There is no need to remove strings from the values. that is, No need to change '10 %' to 10 and '250.00 USD' to 250.\n"
             "Notice that in Excel you can choose Data -> Get Data -> From file -> From PDF to automaticall import tables from a PDF file to you excel.\n"
             "Press Enter to continue")
     else:
        print("Invalid input. Please enter 'y' for Thorlabs format or 'n' for non-Thorlabs format.")
        exit()

items_csv = wait_for_path_from_clipboard(filetype='csv')
df = load_tabular_data(items_csv)

if scientific:
    df = parse_scientific_table(items_csv, thorlabs_format=True)

for _, sample_row in df.iterrows():
    paste_row_to_fields(sample_row)

