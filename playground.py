from core.general_gui_controller import *
import pandas as pd
import winsound
import re

# %%
# record_gui_template(r"tafnit - customs - confirm")
rosh_electroptics_format = True
scientific = True

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
        return None if pd.isna(x) else str(x).strip()
    else:
        return None


def remove_vat(price):
    if isinstance(price, str):
        price = float(price.replace(',', ''))
    return np.ceil(price / 1.18 * 100) / 100 if isinstance(price, (int, float)) else None


def load_tabular_data(path: str) -> pd.DataFrame:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"[ERROR] File does not exist: {path}")

    lower_path = path.lower()

    # Case 1: CSV file
    if lower_path.endswith(".csv"):
        try:
            df = pd.read_csv(path)
        except UnicodeDecodeError:
            winsound.Beep(440, 1000)
            input("The file you are trying to load contains invalid characters. try to save it as UTF-8 encoded CSV and restart the program.")
        return df

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


def parse_quote_table(df: pd.DataFrame, rosh_electroptics_format: bool = False, scientific: bool = True) -> pd.DataFrame:
    # Check the file extension and load the file

    df = df.copy()
    if scientific:
        # Define the target columns in lowercase
        required_columns = ['id', 'description', 'quantity', 'price', 'discount']
        if rosh_electroptics_format:
            # remove the last line of the dataframe if it's Ln value is nan:
            if df.iloc[-1]['Quantity'] == 'TOTAL':
                df = df.iloc[:-1].copy()
            df[['id', 'description']] = df['Part Number and Description'].str.split('\n', n=1, expand=True)
            # rename the column "unit price" to "price":
            df.rename(columns={'Unit Price': 'price'}, inplace=True)
    else:
        required_columns = ['description', 'quantity', 'price', 'note', 'discount']
    # Normalize column names to lowercase for matching
    df.columns = df.columns.str.lower()

    # Allow `name` as a fallback source for `description`.
    if 'description' not in df.columns:
        if 'name' in df.columns:
            df.rename(columns={'name': 'description'}, inplace=True)
        else:
            raise ValueError("[ERROR] Missing required column: expected 'description' or 'name'.")

    # Ensure all required columns exist, adding missing columns as empty
    for col in required_columns:
        if col not in df.columns:
            df[col] = None

    df['price'] = df['price'].apply(clean_number)

    if scientific:
        # Clean the columns
        # Remove disabled items (rows where 'quantity' = 0 or is NaN):

        df['id'] = df['id'].apply(clean_text)
        df['description'] = df['description'].apply(clean_text)
        df['description'] = df['description'].fillna('.')
        # Select and return only the required columns
        df = df.loc[:df.last_valid_index()]
        df = df[required_columns]

    else:
        df['price'] = df['price'].apply(remove_vat)

    # Remove rows where df['description'].lower = 'total' or 'delete_me':
    df['discount'] = df['discount'].apply(clean_number)
    df['discount'] = df['discount'].apply(lambda x: 0 if x is None else x * 100 if x < 1 else x)
    df = df[~df['description'].str.lower().isin(['total', 'delete_me'])]
    df = df[df['quantity'].notna() & (df['quantity'] != 0)].copy()
    df['quantity'] = df['quantity'].apply(clean_number)
    return df

items_csv = 'C:/Users/michaeka/Desktop/kalirkosh example file.xlsx'  # pick_file(filetypes=(("CSV and Excel", "*.csv *.xls *.xlsx"),))
df = load_tabular_data(items_csv)
df = parse_quote_table(df, rosh_electroptics_format=rosh_electroptics_format, scientific=scientific)
print("kaki")