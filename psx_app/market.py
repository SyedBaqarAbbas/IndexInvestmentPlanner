from __future__ import annotations

import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable

import pandas as pd
import requests
from bs4 import BeautifulSoup

KSE100_URL = "https://dps.psx.com.pk/indices/KSE100"
HISTORICAL_URL = "https://dps.psx.com.pk/historical"


def _previous_month_year(month: int, year: int) -> tuple[int, int]:
    if month == 1:
        return 12, year - 1
    return month - 1, year


def _parse_kse100_html(page: bytes) -> pd.DataFrame:
    soup = BeautifulSoup(page, "html.parser")
    header = soup.select_one("thead.tbl__head tr")
    body_rows = soup.select("tbody.tbl__body tr")

    if header is None or not body_rows:
        raise ValueError("Unable to parse KSE-100 table from PSX response.")

    columns = [cell.get_text(strip=True) for cell in header.find_all("th")]
    rows = [[cell.get_text(strip=True) for cell in row.find_all("td")] for row in body_rows]

    if not columns:
        raise ValueError("KSE-100 response did not include table headers.")

    return pd.DataFrame(rows, columns=columns)


def _parse_latest_historical_row(page: bytes) -> dict[str, str] | None:
    soup = BeautifulSoup(page, "html.parser")

    row = soup.select_one("tbody tr")
    if row is None:
        rows = soup.find_all("tr")
        if len(rows) < 2:
            return None
        row = rows[1]

    values = [cell.get_text(strip=True) for cell in row.find_all("td")]
    if len(values) < 6:
        return None

    date_value, open_value, high_value, low_value, close_value, volume_value = values[:6]
    return {
        "DATE": date_value,
        "OPEN": open_value,
        "HIGH": high_value,
        "LOW": low_value,
        "CLOSE": close_value,
        "VOLUME": volume_value,
    }


def get_kse100_data(timeout: int = 20) -> pd.DataFrame:
    response = requests.get(KSE100_URL, timeout=timeout)
    response.raise_for_status()
    return _parse_kse100_html(response.content)


def get_psx_data(
    symbol: str,
    month: int | None = None,
    year: int | None = None,
    lookback_months: int = 18,
    timeout: int = 20,
) -> dict[str, str]:
    now = dt.datetime.now()
    current_month = int(month if month is not None else now.month)
    current_year = int(year if year is not None else now.year)
    max_lookback = max(int(lookback_months), 1)
    normalized_symbol = str(symbol).strip().upper()

    for _ in range(max_lookback):
        response = requests.post(
            HISTORICAL_URL,
            data={
                "month": current_month,
                "year": current_year,
                "symbol": normalized_symbol,
            },
            timeout=timeout,
        )
        response.raise_for_status()

        parsed = _parse_latest_historical_row(response.content)
        if parsed is not None:
            parsed["SYMBOL"] = normalized_symbol
            return parsed

        current_month, current_year = _previous_month_year(current_month, current_year)

    raise ValueError(
        f"No historical PSX data found for symbol={normalized_symbol} "
        f"within {max_lookback} months."
    )


def get_latest_psx_prices(symbols: Iterable[str], max_workers: int = 12) -> dict[str, float]:
    unique_symbols = tuple(
        sorted({str(symbol).strip().upper() for symbol in symbols if str(symbol).strip()})
    )
    if not unique_symbols:
        return {}

    worker_count = max(1, min(max_workers, len(unique_symbols)))

    def _fetch(symbol: str) -> tuple[str, float | None]:
        try:
            row = get_psx_data(symbol=symbol)
            close_value = pd.to_numeric(
                str(row.get("CLOSE", "")).replace(",", ""), errors="coerce"
            )
            if pd.notna(close_value) and float(close_value) > 0:
                return symbol, float(close_value)
        except Exception:
            return symbol, None
        return symbol, None

    prices: dict[str, float] = {}
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {executor.submit(_fetch, symbol): symbol for symbol in unique_symbols}
        for future in as_completed(futures):
            symbol, price = future.result()
            if price is not None:
                prices[symbol] = price

    return prices
