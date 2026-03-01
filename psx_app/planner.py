from __future__ import annotations

import re
from typing import Mapping

import pandas as pd
from securities_parser import PORTFOLIO_ALIASES

PLAN_COLUMNS = ["SYMBOL", "PRICE_TO_INVEST", "CURRENT_PRICE", "SHARES"]
REBALANCE_COLUMNS = [
    "SYMBOL",
    "CURRENT_PRICE",
    "SHARES_CURRENT",
    "SHARES_TARGET",
    "SHARES_TO_TRADE",
    "ACTION",
    "TOTAL_COST",
]

def _canonical_column_name(name: str) -> str:
    normalized = str(name).strip().upper().replace("_", " ")
    return re.sub(r"\s+", " ", normalized)


def _standardize_portfolio_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["SYMBOL", "SHARES", "SHARE PRICE", "TOTAL INVESTED"])

    normalized_df = df.copy()
    normalized_df.columns = [_canonical_column_name(column) for column in normalized_df.columns]

    rename_map: dict[str, str] = {}
    for target, aliases in PORTFOLIO_ALIASES.items():
        for column in normalized_df.columns:
            if column in aliases:
                rename_map[column] = target
                break

    normalized_df = normalized_df.rename(columns=rename_map)
    return normalized_df


def _clean_kse100(kse100_df: pd.DataFrame) -> pd.DataFrame:
    required_columns = {"SYMBOL", "IDX WTG (%)", "CURRENT"}
    missing = required_columns.difference(kse100_df.columns)
    if missing:
        missing_str = ", ".join(sorted(missing))
        raise ValueError(f"KSE-100 data missing required columns: {missing_str}")

    kse = kse100_df.copy()
    kse["SYMBOL"] = (
        kse["SYMBOL"].astype(str).str.replace("XD", "", regex=False).str.strip().str.upper()
    )
    kse["IDX_WEIGHT"] = pd.to_numeric(
        kse["IDX WTG (%)"].astype(str).str.replace("%", "", regex=False), errors="coerce"
    )
    kse["CURRENT_PRICE"] = pd.to_numeric(
        kse["CURRENT"].astype(str).str.replace(",", "", regex=False), errors="coerce"
    )
    kse = kse.dropna(subset=["SYMBOL", "IDX_WEIGHT", "CURRENT_PRICE"])
    kse = kse[kse["SYMBOL"] != ""]
    kse = kse[kse["CURRENT_PRICE"] > 0]

    if kse.empty:
        return kse

    return (
        kse.groupby("SYMBOL", as_index=False)
        .agg(
            IDX_WEIGHT=("IDX_WEIGHT", "sum"),
            CURRENT_PRICE=("CURRENT_PRICE", "first"),
        )
        .reset_index(drop=True)
    )


def _existing_investment_by_symbol(current_portfolio: pd.DataFrame) -> pd.DataFrame:
    normalized = _standardize_portfolio_columns(current_portfolio)
    if "SYMBOL" not in normalized.columns:
        return pd.DataFrame(columns=["SYMBOL", "EXISTING_INVESTED"])

    normalized["SYMBOL"] = normalized["SYMBOL"].astype(str).str.strip().str.upper()
    normalized = normalized[normalized["SYMBOL"] != ""]

    if "TOTAL INVESTED" not in normalized.columns:
        if "SHARE PRICE" in normalized.columns and "SHARES" in normalized.columns:
            normalized["SHARES"] = pd.to_numeric(normalized["SHARES"], errors="coerce").fillna(0)
            normalized["SHARE PRICE"] = pd.to_numeric(
                normalized["SHARE PRICE"], errors="coerce"
            ).fillna(0)
            normalized["TOTAL INVESTED"] = normalized["SHARES"] * normalized["SHARE PRICE"]
        else:
            normalized["TOTAL INVESTED"] = 0.0

    normalized["TOTAL INVESTED"] = pd.to_numeric(
        normalized["TOTAL INVESTED"], errors="coerce"
    ).fillna(0.0)

    return (
        normalized.groupby("SYMBOL", as_index=False)["TOTAL INVESTED"]
        .sum()
        .rename(columns={"TOTAL INVESTED": "EXISTING_INVESTED"})
    )


def _portfolio_holdings(current_portfolio: pd.DataFrame) -> pd.DataFrame:
    normalized = _standardize_portfolio_columns(current_portfolio)
    if "SYMBOL" not in normalized.columns:
        return pd.DataFrame(columns=["SYMBOL", "SHARES_CURRENT", "CURRENT_PRICE_PORTFOLIO"])

    normalized["SYMBOL"] = normalized["SYMBOL"].astype(str).str.strip().str.upper()
    normalized = normalized[normalized["SYMBOL"] != ""]

    if "SHARES" not in normalized.columns:
        normalized["SHARES"] = 0
    if "SHARE PRICE" not in normalized.columns:
        normalized["SHARE PRICE"] = 0.0
    if "TOTAL INVESTED" not in normalized.columns:
        normalized["TOTAL INVESTED"] = pd.to_numeric(
            normalized["SHARES"], errors="coerce"
        ).fillna(0) * pd.to_numeric(normalized["SHARE PRICE"], errors="coerce").fillna(0.0)

    normalized["SHARES"] = pd.to_numeric(normalized["SHARES"], errors="coerce").fillna(0)
    normalized["SHARE PRICE"] = pd.to_numeric(normalized["SHARE PRICE"], errors="coerce").fillna(0.0)
    normalized["TOTAL INVESTED"] = pd.to_numeric(
        normalized["TOTAL INVESTED"], errors="coerce"
    ).fillna(0.0)

    grouped = normalized.groupby("SYMBOL", as_index=False).agg(
        SHARES_CURRENT=("SHARES", "sum"),
        TOTAL_INVESTED=("TOTAL INVESTED", "sum"),
        SHARE_PRICE_FALLBACK=("SHARE PRICE", "mean"),
    )
    grouped["SHARES_CURRENT"] = grouped["SHARES_CURRENT"].round(0).astype(int)
    grouped["CURRENT_PRICE_PORTFOLIO"] = grouped["SHARE_PRICE_FALLBACK"]
    non_zero_shares = grouped["SHARES_CURRENT"] > 0
    grouped.loc[non_zero_shares, "CURRENT_PRICE_PORTFOLIO"] = (
        grouped.loc[non_zero_shares, "TOTAL_INVESTED"]
        / grouped.loc[non_zero_shares, "SHARES_CURRENT"]
    )

    return grouped[["SYMBOL", "SHARES_CURRENT", "CURRENT_PRICE_PORTFOLIO"]]


def determine_action(diff: int) -> str:
    if diff > 0:
        return "BUY"
    if diff < 0:
        return "SELL"
    return "HOLD"


def compare_current_with_index(
    kse100: pd.DataFrame,
    current_portfolio: pd.DataFrame,
    money_to_invest: float,
    threshold: float = 0.0,
) -> pd.DataFrame:
    if money_to_invest <= 0:
        return pd.DataFrame(columns=PLAN_COLUMNS)

    targets = _clean_kse100(kse100)
    if targets.empty:
        return pd.DataFrame(columns=PLAN_COLUMNS)

    targets["TARGET_INVESTMENT"] = money_to_invest * (targets["IDX_WEIGHT"] / 100.0)
    existing = _existing_investment_by_symbol(current_portfolio)
    merged = pd.merge(targets, existing, on="SYMBOL", how="left")
    merged["EXISTING_INVESTED"] = pd.to_numeric(
        merged["EXISTING_INVESTED"], errors="coerce"
    ).fillna(0.0)
    merged["PRICE_TO_INVEST"] = (merged["TARGET_INVESTMENT"] - merged["EXISTING_INVESTED"]).clip(
        lower=0
    )
    merged["SHARES"] = (
        (merged["PRICE_TO_INVEST"] // merged["CURRENT_PRICE"])
        .replace([float("inf"), float("-inf")], 0)
        .fillna(0)
        .astype(int)
    )

    threshold_value = float(threshold or 0.0)
    if threshold_value > 0:
        threshold_mask = (
            (merged["EXISTING_INVESTED"] <= 0)
            & (merged["SHARES"] == 0)
            & (merged["CURRENT_PRICE"] <= threshold_value)
        )
        merged.loc[threshold_mask, "SHARES"] = 1
        merged.loc[threshold_mask, "PRICE_TO_INVEST"] = merged.loc[
            threshold_mask, "CURRENT_PRICE"
        ]

    result = merged.loc[merged["SHARES"] > 0, PLAN_COLUMNS].copy()
    result["PRICE_TO_INVEST"] = result["PRICE_TO_INVEST"].round(2)
    result["CURRENT_PRICE"] = result["CURRENT_PRICE"].round(2)
    result = result.sort_values(by="PRICE_TO_INVEST", ascending=False)
    return result.reset_index(drop=True)


def get_non_index_symbols(kse100_df: pd.DataFrame, current_portfolio_df: pd.DataFrame) -> tuple[str, ...]:
    kse_symbols = set(_clean_kse100(kse100_df)["SYMBOL"].tolist())
    current_symbols = set(_portfolio_holdings(current_portfolio_df)["SYMBOL"].tolist())
    return tuple(sorted(current_symbols - kse_symbols))


def build_rebalance_plan(
    kse100_df: pd.DataFrame,
    current_portfolio_df: pd.DataFrame,
    target_portfolio_value: float,
    extra_symbol_prices: Mapping[str, float] | None = None,
) -> pd.DataFrame:
    targets = _clean_kse100(kse100_df)
    holdings = _portfolio_holdings(current_portfolio_df)

    if targets.empty and holdings.empty:
        return pd.DataFrame(columns=REBALANCE_COLUMNS)

    targets["SHARES_TARGET"] = (
        (target_portfolio_value * (targets["IDX_WEIGHT"] / 100.0) / targets["CURRENT_PRICE"])
        .replace([float("inf"), float("-inf")], 0)
        .fillna(0)
        .round(0)
        .astype(int)
    )

    target_df = targets[["SYMBOL", "CURRENT_PRICE", "SHARES_TARGET"]].copy()
    merged = pd.merge(target_df, holdings, on="SYMBOL", how="outer")

    merged["SHARES_TARGET"] = pd.to_numeric(merged["SHARES_TARGET"], errors="coerce").fillna(0).astype(int)
    merged["SHARES_CURRENT"] = (
        pd.to_numeric(merged["SHARES_CURRENT"], errors="coerce").fillna(0).astype(int)
    )
    merged["CURRENT_PRICE"] = pd.to_numeric(merged["CURRENT_PRICE"], errors="coerce")

    if extra_symbol_prices:
        normalized_prices = {
            str(symbol).strip().upper(): float(price)
            for symbol, price in extra_symbol_prices.items()
            if symbol is not None
        }
        merged["CURRENT_PRICE"] = merged["CURRENT_PRICE"].fillna(
            merged["SYMBOL"].astype(str).str.upper().map(normalized_prices)
        )

    merged["CURRENT_PRICE"] = merged["CURRENT_PRICE"].fillna(merged["CURRENT_PRICE_PORTFOLIO"]).fillna(0.0)
    merged["CURRENT_PRICE"] = pd.to_numeric(merged["CURRENT_PRICE"], errors="coerce").fillna(0.0)

    merged["DIFF"] = merged["SHARES_TARGET"] - merged["SHARES_CURRENT"]
    merged["ACTION"] = merged["DIFF"].apply(determine_action)
    merged["SHARES_TO_TRADE"] = merged["DIFF"].abs().astype(int)

    merged["TOTAL_COST"] = 0.0
    buy_mask = merged["ACTION"] == "BUY"
    sell_mask = merged["ACTION"] == "SELL"
    merged.loc[buy_mask, "TOTAL_COST"] = (
        merged.loc[buy_mask, "SHARES_TO_TRADE"] * merged.loc[buy_mask, "CURRENT_PRICE"]
    )
    merged.loc[sell_mask, "TOTAL_COST"] = -(
        merged.loc[sell_mask, "SHARES_TO_TRADE"] * merged.loc[sell_mask, "CURRENT_PRICE"]
    )

    result = merged[REBALANCE_COLUMNS].copy()
    result["CURRENT_PRICE"] = result["CURRENT_PRICE"].round(2)
    result["TOTAL_COST"] = result["TOTAL_COST"].round(2)

    action_order = pd.Categorical(
        result["ACTION"],
        categories=["BUY", "SELL", "HOLD"],
        ordered=True,
    )
    result = (
        result.assign(_ACTION_ORDER=action_order)
        .sort_values(by=["_ACTION_ORDER", "SHARES_TO_TRADE"], ascending=[True, False])
        .drop(columns="_ACTION_ORDER")
    )
    return result.reset_index(drop=True)
