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


def parse_scientific_table(file_path, scientific=True, thorlabs_format=True):
    # Check the file extension and load the file
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Please select a .csv or .xlsx file.")

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
      "When you will need to choose supplier or a quote file in Tafnit, the script will wait for you to choose it,\nand after"
      "choosing, you will not to go back here and press enter\n"
      "Press Enter to continue")
scientific_or_food_text = input("If this is a scientific purchase, press s, and if it is a food purchase, press f.\n")
if scientific_or_food_text.lower() == 's':
    scientific = True
elif scientific_or_food_text.lower() == 'f':
    scientific = False
else:
    print("Invalid input. Please enter 's' for scientific or 'f' for food.")
    exit()



BOX_LL = (3, 1072)  #  get_cursor_position("lower-left corner of the tafnit window")
BOX_UR = (1916, 4)  #  get_cursor_position("upper-right corner of the tafnit window")
SLEEP_TIME = 0.2
LONG_SLEEP_TIME = 2
# %% Main menu navigation::
button_position = detect_position('ivrit - main.png', relative_position=(0.5, 0.3),
                                  crop_ll=BOX_LL, crop_ur=BOX_UR, click=True, sleep=SLEEP_TIME)

button_position = detect_position('yazam.png', relative_position=(0.5, 0.3),
                                  crop_ll=BOX_LL, crop_ur=BOX_UR, click=True, sleep=SLEEP_TIME)

button_position = detect_position('ivrit - secondary.png',
                                  crop_ll=BOX_LL, crop_ur=BOX_UR, click=True, sleep=LONG_SLEEP_TIME)
button_position = detect_position('klita.png',
                                  crop_ll=BOX_LL, crop_ur=BOX_UR, click=True)
pyautogui.moveTo(2, 2)
time.sleep(LONG_SLEEP_TIME)

if scientific:
    button_position = detect_position("drisha lerechesh.png",
                                          crop_ll=BOX_LL, crop_ur=BOX_UR, click=True, sleep=8)
else:
    button_position = detect_position('hazmana kaspit sherutim.png',
                                      crop_ll=BOX_LL, crop_ur=BOX_UR, click=True, sleep=8)

# %% Supplier selection:
button_position = detect_position('sapak.png',
                                  crop_ll=BOX_LL, crop_ur=BOX_UR, click=True, sleep=2)

button_position = detect_position('sochen.png', relative_position=(1.6, 0.5),
                                  crop_ll=BOX_LL, crop_ur=BOX_UR, click=True, sleep=2)

continue_keyword = input("Choose the quote from the list, go back here, and press enter to continue or s to stop and exit\n")
if continue_keyword.lower() == 'e':
    exit()

minimize_current_window()

# %% Upload quote:
nispachim_position = detect_position('nispachim.png',
                                     crop_ll=BOX_LL, crop_ur=BOX_UR)
pyautogui.click(nispachim_position)
sleep(3)

sherutei_archive_position = detect_position('sherutei archive.png',
                                            crop_ll=BOX_LL, crop_ur=BOX_UR, sleep=SLEEP_TIME, click=True)

teur_mismach_position = detect_position('teur mismach.png',
                                        crop_ll=BOX_LL, crop_ur=BOX_UR, relative_position=(0.1, 0.5), click=True, sleep=SLEEP_TIME)

pyautogui.write('quote')

haalaa_lasharat_position = detect_position('haalaa lasharat.png',
                                           crop_ll=BOX_LL, crop_ur=BOX_UR, click=True, sleep=LONG_SLEEP_TIME)


bechar_kovets_position = detect_position('bechar kovets.png',
                                         crop_ll=BOX_LL, crop_ur=BOX_UR, click=True)
continue_keyword = input("Choose the quote from the list, go back here, and press enter to continue or s to stop and exit\n")
if continue_keyword.lower() == 'e':
    exit()
minimize_current_window()
ishur_upload_position = detect_position('ishur - upload.png',
                                        crop_ll=BOX_LL, crop_ur=BOX_UR, relative_position=(0.8, 0.5),
                                        minimal_confidence=0.97, click=True, sleep=LONG_SLEEP_TIME)


# %%

pritim_position = detect_position('pritim.png',
                                  crop_ll=BOX_LL, crop_ur=BOX_UR, click=True, sleep=LONG_SLEEP_TIME)

makat_position = detect_position('makat_sapak.png',relative_position = (-0.945, 0.542),
                                 crop_ll=BOX_LL, crop_ur=BOX_UR, click=False)

hanacha_position = detect_position('hanacha.png', relative_position=(-0.822, 0.571),
                                      crop_ll=BOX_LL, crop_ur=BOX_UR, click=False)

teur_position = detect_position('teur.png', relative_position=(-1, 0.5),
                                crop_ll=BOX_LL, crop_ur=BOX_UR, click=False)

kamut_position = detect_position('kamut.png', relative_position=(-1, 0.5),
                                 crop_ll=BOX_LL, crop_ur=BOX_UR, click=False)

mechir_bematbea_position = detect_position('mechir bematbea.png', relative_position=(-1, 0.5),
                                           crop_ll=BOX_LL, crop_ur=BOX_UR, click=False)

adken_shura_position = detect_position('adken shura.png',
                                       crop_ll=BOX_LL, crop_ur=BOX_UR, click=False)

# %%

category_1_position = detect_position('categories.png', relative_position=(-0.4, 0.85),
                                      crop_ll=BOX_LL, crop_ur=BOX_UR, click=True, sleep=SLEEP_TIME)
if scientific:
    category_1_choice_position = detect_position('scientific equipment.png',
                                                 relative_position=(0.5, 0.5), crop_ll=BOX_LL, crop_ur=BOX_UR,
                                                 click=True, sleep=SLEEP_TIME)
else:
    category_1_choice_position = detect_position('sherutim.png', relative_position=(0.9, 0.5),
                                        crop_ll=BOX_LL, crop_ur=BOX_UR, click=True, sleep=SLEEP_TIME)

category_2_position = detect_position('categories.png', relative_position=(-0.4, 0.65),
                                      crop_ll=BOX_LL, crop_ur=BOX_UR, click=True, sleep=SLEEP_TIME)
if scientific:
    category_2_choice_position = detect_position('laboratory instruments.png',
                                                 relative_position=(0.5, 0.5), crop_ll=BOX_LL, crop_ur=BOX_UR,
                                                 sleep=SLEEP_TIME, click=True)
else:
    category_2_choice_position = detect_position('eruim kibud achzaka.png',
                                                 crop_ll=BOX_LL, crop_ur=BOX_UR, click=True, sleep=SLEEP_TIME)
if not scientific:
    category_3_position = detect_position('categories.png', relative_position=(-0.4, 0.35),
                                          crop_ll=BOX_LL, crop_ur=BOX_UR, click=True, sleep=SLEEP_TIME)

    category_3_choice_position = detect_position('kibud kal.png',
                                                 crop_ll=BOX_LL, crop_ur=BOX_UR, click=True, sleep=SLEEP_TIME)

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

if scientific:
    df = parse_scientific_table(items_csv, thorlabs_format=True)
else:
    df = pd.read_csv(items_csv)

for _, sample_row in df.iterrows():
    paste_row_to_fields(sample_row)

