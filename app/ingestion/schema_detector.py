import pandas as pd
from typing import Dict, List


def detect_schema(df: pd.DataFrame) -> Dict:
    """
    Automatically detect the schema of an uploaded dataset.
    Returns:
      - time_columns: columns that look like dates
      - metric_columns: numeric columns
      - category_columns: text/low-cardinality columns
    """
    time_columns = []
    metric_columns = []
    category_columns = []

    for col in df.columns:

        # --- Already a datetime dtype ---
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            time_columns.append(col)
            continue

        # --- Try to detect time columns from string columns ---
        if df[col].dtype == "object" or str(df[col].dtype) == "str":

            # Check column name hints first (fast path)
            name_hints = ["date", "time", "month", "year", "week", "period", "quarter"]
            col_lower = col.lower()
            is_name_hint = any(hint in col_lower for hint in name_hints)

            # Try multiple date formats
            date_formats = [
                "%Y-%m-%d",    # 2024-01-01
                "%m/%d/%Y",    # 01/01/2024
                "%m/%d/%y",    # 1/1/24
                "%d-%m-%Y",    # 01-01-2024
                "%B %Y",       # January 2024
                "%b %Y",       # Jan 2024
                "%Y-%m",       # 2024-01
                "%Y",          # 2024
            ]

            parsed_successfully = False

            # Try each format explicitly first
            for fmt in date_formats:
                try:
                    parsed = pd.to_datetime(df[col], format=fmt, errors="coerce")
                    if parsed.notna().sum() > len(df) * 0.5:
                        time_columns.append(col)
                        parsed_successfully = True
                        break
                except Exception:
                    continue

            if parsed_successfully:
                continue

            # Fall back to pandas inference
            try:
                parsed = pd.to_datetime(df[col], errors="coerce", infer_datetime_format=True)
                if parsed.notna().sum() > len(df) * 0.7:
                    time_columns.append(col)
                    continue
            except Exception:
                pass

            # Last resort: if column name is a date hint, try harder
            if is_name_hint:
                try:
                    parsed = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
                    if parsed.notna().sum() > len(df) * 0.5:
                        time_columns.append(col)
                        continue
                except Exception:
                    pass

        # --- Detect numeric metric columns ---
        if pd.api.types.is_numeric_dtype(df[col]):
            metric_columns.append(col)
            continue

        # --- Everything else is a category ---
        category_columns.append(col)

    return {
        "time_columns": time_columns,
        "metric_columns": metric_columns,
        "category_columns": category_columns
    }


def validate_schema(schema: Dict) -> Dict:
    """
    Validate that the dataset has minimum required structure.
    """
    errors = []

    if not schema["time_columns"]:
        errors.append("No date/time column detected. At least one time column is required.")

    if not schema["metric_columns"]:
        errors.append("No numeric metric columns detected. At least one metric is required.")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }