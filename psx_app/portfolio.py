from __future__ import annotations

from io import BytesIO

import pandas as pd

from securities_parser import (
    normalize_portfolio_df,
    parse_securities_pdf_bytes,
    portfolio_from_parsed_rows,
)


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def parse_statement_pdf(pdf_bytes: bytes) -> tuple[pd.DataFrame, pd.DataFrame]:
    parsed_rows = parse_securities_pdf_bytes(pdf_bytes)
    portfolio_df = portfolio_from_parsed_rows(parsed_rows)
    return parsed_rows, portfolio_df


def load_portfolio_csv(path: str) -> pd.DataFrame:
    return normalize_portfolio_df(pd.read_csv(path))


def load_portfolio_csv_bytes(csv_bytes: bytes) -> pd.DataFrame:
    return normalize_portfolio_df(pd.read_csv(BytesIO(csv_bytes)))
