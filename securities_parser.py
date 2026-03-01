import re
from typing import Dict

import pandas as pd

RAW_COLUMNS = [
    "Shares_Value",
    "Available_Qty",
    "Price",
    "Symbol",
    "UIN",
    "CDS_Account_No",
    "Participant_ID",
    "Inventory_Date",
]

PORTFOLIO_COLUMNS = ["SYMBOL", "SHARE PRICE", "SHARES", "TOTAL INVESTED"]

SECURITIES_PATTERN = re.compile(
    r"(?P<Shares_Value>[\d,]+\.\d+)\s*"
    r"(?P<Available_Qty>[\d,]+)\s*"
    r"(?P<Price>[\d,]+\.\d+)\s*"
    r"(?P<Symbol>[A-Z0-9]+)\s*"
    r"(?P<UIN>\d{13})\s*"
    r"(?P<CDS_Account_No>\d+)\s*"
    r"(?P<Participant_ID>\d+)\s*"
    r"(?P<Inventory_Date>\d{2}/\d{2}/\d{4})"
)

PORTFOLIO_ALIASES: Dict[str, set[str]] = {
    "SYMBOL": {"SYMBOL", "NAME"},
    "SHARE PRICE": {
        "SHARE PRICE",
        "SHAREPRICE",
        "SHARE_PRICE",
        "AVG PRICE",
        "AVERAGE PRICE",
        "CURRENT PRICE",
        "PRICE",
    },
    "SHARES": {
        "SHARES",
        "QTY",
        "QUANTITY",
        "AVAILABLE",
        "AVAILABLE QTY",
        "POSITION OWNED",
    },
    "TOTAL INVESTED": {
        "TOTAL INVESTED",
        "TOTALINVESTED",
        "TOTAL_INVESTED",
        "SHARES VALUE",
        "VALUE",
        "AMOUNT",
    },
}


def _canonical_column_name(name: str) -> str:
    normalized = str(name).strip().upper().replace("_", " ")
    return re.sub(r"\s+", " ", normalized)


def _ensure_fitz():
    try:
        import fitz  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF is required for PDF parsing. Install dependency 'PyMuPDF'."
        ) from exc
    return fitz


def empty_portfolio_df() -> pd.DataFrame:
    return pd.DataFrame(columns=PORTFOLIO_COLUMNS)


def parse_securities_pdf_bytes(pdf_bytes: bytes) -> pd.DataFrame:
    if not pdf_bytes:
        return pd.DataFrame(columns=RAW_COLUMNS)

    fitz = _ensure_fitz()
    rows = []

    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            for block in page.get_text("blocks"):
                block_text = block[4]
                for match in SECURITIES_PATTERN.finditer(block_text):
                    rows.append(match.groupdict())

    if not rows:
        return pd.DataFrame(columns=RAW_COLUMNS)

    df = pd.DataFrame(rows)

    numeric_columns = [
        "Shares_Value",
        "Available_Qty",
        "Price",
        "UIN",
        "CDS_Account_No",
        "Participant_ID",
    ]
    for column in numeric_columns:
        cleaned = df[column].astype(str).str.replace(",", "", regex=False)
        df[column] = pd.to_numeric(cleaned, errors="coerce")

    df["Inventory_Date"] = pd.to_datetime(
        df["Inventory_Date"], format="%d/%m/%Y", errors="coerce"
    )
    df["Symbol"] = df["Symbol"].astype(str).str.strip().str.upper()

    df = df.dropna(subset=["Symbol", "Shares_Value", "Available_Qty"])
    return df[RAW_COLUMNS].reset_index(drop=True)


def portfolio_from_parsed_rows(parsed_df: pd.DataFrame) -> pd.DataFrame:
    if parsed_df.empty:
        return empty_portfolio_df()

    grouped = (
        parsed_df.groupby("Symbol", as_index=False)
        .agg(
            SHARES=("Available_Qty", "sum"),
            TOTAL_INVESTED=("Shares_Value", "sum"),
        )
        .rename(columns={"Symbol": "SYMBOL"})
    )
    grouped["SHARE PRICE"] = grouped["TOTAL_INVESTED"] / grouped["SHARES"]
    grouped["SHARES"] = grouped["SHARES"].round(0).astype(int)
    grouped = grouped.rename(columns={"TOTAL_INVESTED": "TOTAL INVESTED"})
    grouped = grouped[PORTFOLIO_COLUMNS]
    grouped = grouped.sort_values(by="TOTAL INVESTED", ascending=False)
    return grouped.reset_index(drop=True)


def normalize_portfolio_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return empty_portfolio_df()

    normalized_df = df.copy()
    normalized_df.columns = [_canonical_column_name(column) for column in df.columns]

    rename_map = {}
    for target, aliases in PORTFOLIO_ALIASES.items():
        for column in normalized_df.columns:
            if column in aliases:
                rename_map[column] = target
                break

    normalized_df = normalized_df.rename(columns=rename_map)

    if "SYMBOL" not in normalized_df.columns or "SHARES" not in normalized_df.columns:
        raise ValueError(
            "Portfolio file must include symbol and shares columns. "
            "Expected at least SYMBOL and SHARES/QTY."
        )

    if "TOTAL INVESTED" not in normalized_df.columns and "SHARE PRICE" not in normalized_df.columns:
        raise ValueError(
            "Portfolio file must include SHARE PRICE or TOTAL INVESTED."
        )

    for numeric_column in ["SHARES", "SHARE PRICE", "TOTAL INVESTED"]:
        if numeric_column in normalized_df.columns:
            normalized_df[numeric_column] = pd.to_numeric(
                normalized_df[numeric_column], errors="coerce"
            )

    if "TOTAL INVESTED" not in normalized_df.columns:
        normalized_df["TOTAL INVESTED"] = normalized_df["SHARE PRICE"] * normalized_df["SHARES"]
    if "SHARE PRICE" not in normalized_df.columns:
        normalized_df["SHARE PRICE"] = normalized_df["TOTAL INVESTED"] / normalized_df["SHARES"]

    normalized_df["SYMBOL"] = normalized_df["SYMBOL"].astype(str).str.strip().str.upper()
    normalized_df = normalized_df.dropna(subset=["SYMBOL", "SHARES", "SHARE PRICE", "TOTAL INVESTED"])
    normalized_df = normalized_df[normalized_df["SYMBOL"] != ""]
    normalized_df = normalized_df[normalized_df["SHARES"] > 0]

    normalized_df = normalized_df[PORTFOLIO_COLUMNS]
    normalized_df = normalized_df.sort_values(by="TOTAL INVESTED", ascending=False)
    return normalized_df.reset_index(drop=True)
