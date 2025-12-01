import pandas as pd
from typing import List, Optional, Tuple

INTERVAL_LOOKUP = {
    "1": 1,
    "2": 2,
    "5": 5,
    "10": 10,
    "30": 30,
    "60": 60,
    "Day": 60,   # placeholder; map Day/Week/Month as needed
    "Week": 60,
    "Month": 60,
}


def read_tokens_and_interval(xlsx_path: str,
                              token_col: str = "A",
                              interval_col: Optional[str] = None) -> Tuple[List[str], Optional[int]]:
    """
    Reads tokens from Column A. Optionally reads interval from a column (X).
    Returns (tokens, interval_minutes or None)
    """
    df = pd.read_excel(xlsx_path, header=None)
    # Column names are numbers; A=0, B=1, ..., X=23
    col_map = {chr(ord('A') + i): i for i in range(df.shape[1])}
    tokens: List[str] = []
    if token_col not in col_map:
        raise ValueError(f"Token column {token_col} not found in sheet")
    for val in df.iloc[:, col_map[token_col]].dropna().tolist():
        s = str(val).strip()
        if s:
            tokens.append(s)

    interval_val: Optional[int] = None
    if interval_col:
        if interval_col not in col_map:
            raise ValueError(f"Interval column {interval_col} not found in sheet")
        raw = df.iloc[0, col_map[interval_col]]
        if pd.notna(raw):
            key = str(raw).strip()
            interval_val = INTERVAL_LOOKUP.get(key)

    return tokens, interval_val
