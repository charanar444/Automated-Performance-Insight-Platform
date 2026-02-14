import pandas as pd
from fastapi import UploadFile


def load_file(file: UploadFile) -> pd.DataFrame:
    """
    Load CSV or Excel file into a clean Pandas DataFrame.
    Handles: missing values, messy headers, duplicates, encoding issues.
    """
    filename = file.filename.lower()

    # --- Load file ---
    if filename.endswith(".csv"):
        try:
            df = pd.read_csv(file.file, encoding="utf-8")
        except UnicodeDecodeError:
            file.file.seek(0)
            df = pd.read_csv(file.file, encoding="latin-1")

    elif filename.endswith((".xls", ".xlsx")):
        df = pd.read_excel(file.file)

    else:
        raise ValueError("Unsupported file type. Please upload CSV or Excel.")

    if df.empty:
        raise ValueError("Uploaded file is empty.")

    # --- Clean column names ---
    # strips spaces, lowercases, replaces spaces with underscores
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace(r"[^\w]", "_", regex=True)
    )

    # --- Remove fully empty rows and columns ---
    df.dropna(how="all", inplace=True)
    df.dropna(axis=1, how="all", inplace=True)

    # --- Remove duplicate rows ---
    df.drop_duplicates(inplace=True)

    # --- Reset index after cleaning ---
    df.reset_index(drop=True, inplace=True)

    if df.empty:
        raise ValueError("File has no usable data after cleaning.")

    return df