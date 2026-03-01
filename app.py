from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import streamlit as st

from psx import compare_current_with_index, get_kse100_data, get_psx_data
from securities_parser import (
    empty_portfolio_df,
    normalize_portfolio_df,
    parse_securities_pdf_bytes,
    portfolio_from_parsed_rows,
)

st.set_page_config(page_title="KSE-100 Tracker", page_icon=":chart_with_upwards_trend:", layout="wide")


@st.cache_data
def convert_for_download(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def determine_action(diff: int) -> str:
    if diff > 0:
        return "BUY"
    if diff < 0:
        return "SELL"
    return "HOLD"


@st.cache_data(show_spinner=False, ttl=900)
def fetch_latest_psx_prices(symbols: tuple[str, ...]) -> dict[str, float]:
    def _fetch(symbol: str) -> tuple[str, float | None]:
        try:
            row = get_psx_data(symbol=symbol)
            close_value = pd.to_numeric(
                str(row.get("CLOSE", "")).replace(",", ""), errors="coerce"
            )
            if pd.notna(close_value) and float(close_value) > 0:
                return symbol, float(close_value)
        except Exception:
            pass
        return symbol, None

    prices: dict[str, float] = {}
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(_fetch, symbol): symbol for symbol in symbols}
        for future in as_completed(futures):
            symbol, price = future.result()
            if price is not None:
                prices[symbol] = price
    return prices


def build_rebalance_plan(
    kse100_df: pd.DataFrame,
    current_portfolio_df: pd.DataFrame,
    target_portfolio_value: float,
    extra_symbol_prices: dict[str, float],
) -> pd.DataFrame:
    kse = kse100_df.copy()
    kse["SYMBOL"] = kse["SYMBOL"].astype(str).str.replace("XD", "", regex=False).str.strip().str.upper()
    kse["KSE_CURRENT_PRICE"] = pd.to_numeric(
        kse["CURRENT"].astype(str).str.replace(",", "", regex=False), errors="coerce"
    )
    # For KSE-100 symbols, use the index endpoint price directly.
    kse["CURRENT_PRICE"] = kse["KSE_CURRENT_PRICE"]
    kse["IDX_WEIGHT"] = pd.to_numeric(
        kse["IDX WTG (%)"].astype(str).str.replace("%", "", regex=False), errors="coerce"
    )
    kse["SHARES_TARGET"] = (
        (target_portfolio_value * (kse["IDX_WEIGHT"] / 100.0) / kse["CURRENT_PRICE"])
        .replace([float("inf"), float("-inf")], 0)
        .fillna(0)
        .round(0)
        .astype(int)
    )
    target_df = (
        kse[["SYMBOL", "CURRENT_PRICE", "SHARES_TARGET"]]
        .groupby("SYMBOL", as_index=False)
        .agg(CURRENT_PRICE=("CURRENT_PRICE", "first"), SHARES_TARGET=("SHARES_TARGET", "sum"))
    )

    current_df = current_portfolio_df.copy()
    if current_df.empty:
        current_df = pd.DataFrame(columns=["SYMBOL", "SHARES", "SHARE PRICE"])
    current_df["SYMBOL"] = current_df["SYMBOL"].astype(str).str.strip().str.upper()
    current_df["SHARES"] = pd.to_numeric(current_df["SHARES"], errors="coerce").fillna(0)
    current_df["SHARE PRICE"] = pd.to_numeric(current_df["SHARE PRICE"], errors="coerce")
    current_df = current_df.rename(
        columns={"SHARES": "SHARES_CURRENT", "SHARE PRICE": "CURRENT_PRICE_PORTFOLIO"}
    )
    current_df = current_df[["SYMBOL", "SHARES_CURRENT", "CURRENT_PRICE_PORTFOLIO"]]

    merged = pd.merge(target_df, current_df, on="SYMBOL", how="outer")
    merged["SHARES_TARGET"] = pd.to_numeric(merged["SHARES_TARGET"], errors="coerce").fillna(0).astype(int)
    merged["SHARES_CURRENT"] = pd.to_numeric(merged["SHARES_CURRENT"], errors="coerce").fillna(0).astype(int)
    merged["CURRENT_PRICE"] = merged["CURRENT_PRICE"].fillna(merged["SYMBOL"].map(extra_symbol_prices))
    merged["CURRENT_PRICE"] = merged["CURRENT_PRICE"].fillna(merged["CURRENT_PRICE_PORTFOLIO"]).fillna(0.0)

    merged["DIFF"] = merged["SHARES_TARGET"] - merged["SHARES_CURRENT"]
    merged["ACTION"] = merged["DIFF"].apply(determine_action)
    merged["SHARES_TO_TRADE"] = merged["DIFF"].abs().astype(int)
    merged["TOTAL_COST"] = merged.apply(
        lambda row: row["SHARES_TO_TRADE"] * row["CURRENT_PRICE"]
        if row["ACTION"] == "BUY"
        else -row["SHARES_TO_TRADE"] * row["CURRENT_PRICE"]
        if row["ACTION"] == "SELL"
        else 0.0,
        axis=1,
    )

    result = merged[
        [
            "SYMBOL",
            "CURRENT_PRICE",
            "SHARES_CURRENT",
            "SHARES_TARGET",
            "SHARES_TO_TRADE",
            "ACTION",
            "TOTAL_COST",
        ]
    ].copy()
    result["CURRENT_PRICE"] = result["CURRENT_PRICE"].round(2)
    result["TOTAL_COST"] = result["TOTAL_COST"].round(2)
    result = result.sort_values(by=["ACTION", "SHARES_TO_TRADE"], ascending=[True, False])
    return result.reset_index(drop=True)


def color_action_rows(row: pd.Series) -> list[str]:
    action = row.get("ACTION", "")
    if action == "BUY":
        color = "rgba(34, 197, 94, 0.18)"
    elif action == "SELL":
        color = "rgba(239, 68, 68, 0.18)"
    else:
        color = "rgba(127, 127, 127, 0.08)"
    return [f"background-color: {color}" for _ in row]


@st.cache_data(show_spinner=False)
def parse_uploaded_statement(pdf_bytes: bytes) -> tuple[pd.DataFrame, pd.DataFrame]:
    parsed_rows = parse_securities_pdf_bytes(pdf_bytes)
    portfolio = portfolio_from_parsed_rows(parsed_rows)
    return parsed_rows, portfolio


st.markdown(
    """
    <style>
      .block-container {
          padding-top: 1.2rem;
          padding-bottom: 2rem;
      }
      .hero-card {
          border: 1px solid rgba(127, 127, 127, 0.28);
          border-radius: 16px;
          padding: 1.1rem 1.2rem;
          background: linear-gradient(
            125deg,
            var(--secondary-background-color) 0%,
            var(--background-color) 100%
          );
          color: var(--text-color);
      }
      .source-card {
          border: 1px solid rgba(127, 127, 127, 0.22);
          border-radius: 14px;
          padding: 0.9rem 1rem;
          background: var(--secondary-background-color);
          color: var(--text-color);
      }
      [data-testid="stMetric"] {
          border: 1px solid rgba(127, 127, 127, 0.2);
          border-radius: 12px;
          background: var(--secondary-background-color);
          padding: 0.5rem 0.7rem;
          color: var(--text-color);
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-card">
      <h2 style="margin:0 0 0.3rem 0;">KSE-100 Investment Planner</h2>
      <p style="margin:0;">
        Upload your current holdings (PDF statement or CSV), then generate a buy plan aligned with KSE-100 weightage.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")
money_to_invest = st.number_input(
    "Target Portfolio Value (PKR)",
    min_value=0.0,
    value=300000.0,
    step=1000.0,
    help="Total portfolio value you want this plan to target.",
)
sell_non_kse100 = st.toggle(
    "Sell existing stocks for rebalancing?",
    value=False,
    help=(
        "Off: keep non-index holdings and show buy-only recommended investment plan. "
        "On: allow selling and show full rebalance actions."
        "Set to off if you want to retain your existing holdings while rebalancing."
    ),
)

st.markdown('<div class="source-card">', unsafe_allow_html=True)
portfolio_source = st.radio(
    "Current Portfolio Source",
    options=["Upload Securities PDF", "Upload Portfolio CSV", "No current portfolio"],
    horizontal=True,
)
portfolio_df = empty_portfolio_df()
parsed_rows_df = pd.DataFrame()
input_is_valid = True

if portfolio_source == "Upload Securities PDF":
    uploaded_pdf = st.file_uploader("Upload securities statement (.pdf)", type=["pdf"])
    if uploaded_pdf is not None:
        try:
            parsed_rows_df, portfolio_df = parse_uploaded_statement(uploaded_pdf.getvalue())
            if portfolio_df.empty:
                input_is_valid = False
                st.warning("No holdings were parsed from the uploaded statement.")
            else:
                st.success("Securities statement parsed successfully.")
        except Exception as exc:
            input_is_valid = False
            st.error(f"Unable to parse PDF statement: {exc}")
    else:
        input_is_valid = False

if portfolio_source == "Upload Portfolio CSV":
    uploaded_csv = st.file_uploader("Upload current portfolio (.csv)", type=["csv"])
    if uploaded_csv is not None:
        try:
            csv_df = pd.read_csv(uploaded_csv)
            portfolio_df = normalize_portfolio_df(csv_df)
            st.success("Portfolio CSV loaded.")
        except Exception as exc:
            input_is_valid = False
            st.error(f"Unable to parse CSV: {exc}")
    else:
        input_is_valid = False

if portfolio_source == "No current portfolio":
    st.info("Plan will be generated as if you have no existing holdings.")

st.markdown("</div>", unsafe_allow_html=True)

preview_col, metric_col = st.columns([2.2, 1.2])
with preview_col:
    if portfolio_source == "Upload Securities PDF":
        st.subheader(
            "Current Portfolio Preview",
            help=(
                "For uploaded securities statements, SHARE PRICE is your average buy price "
                "parsed from the statement, not the latest market price."
            ),
        )
    else:
        st.subheader("Current Portfolio Preview")
    if portfolio_df.empty:
        st.caption("No portfolio loaded yet.")
    else:
        column_config = None
        if portfolio_source == "Upload Securities PDF":
            column_config = {
                "SHARE PRICE": st.column_config.NumberColumn(
                    "SHARE PRICE",
                    help="Average buy price from your uploaded PDF statement.",
                )
            }
        st.dataframe(
            portfolio_df,
            use_container_width=True,
            hide_index=True,
            column_config=column_config,
        )

with metric_col:
    st.subheader("Portfolio Snapshot")
    total_symbols = int(portfolio_df["SYMBOL"].nunique()) if not portfolio_df.empty else 0
    total_shares = int(portfolio_df["SHARES"].sum()) if not portfolio_df.empty else 0
    total_invested = float(portfolio_df["TOTAL INVESTED"].sum()) if not portfolio_df.empty else 0.0
    st.metric("Symbols", f"{total_symbols}")
    st.metric("Shares", f"{total_shares:,}")
    st.metric("Invested", f"PKR {total_invested:,.0f}")

if portfolio_source == "Upload Securities PDF" and not parsed_rows_df.empty:
    with st.expander("View parsed securities rows"):
        st.dataframe(parsed_rows_df, use_container_width=True, hide_index=True)
        st.download_button(
            label="Download Parsed Rows",
            data=convert_for_download(parsed_rows_df),
            file_name="parsed_securities_rows.csv",
            mime="text/csv",
            use_container_width=True,
        )

generate_plan = st.button("Generate Investment Plan", type="primary", use_container_width=True)

if generate_plan:
    if money_to_invest <= 0:
        st.error("Enter a target portfolio value greater than zero.")
    elif portfolio_source != "No current portfolio" and not input_is_valid:
        st.error("Upload a valid portfolio file before generating the plan.")
    else:
        investment_plan = pd.DataFrame()
        rebalance_plan = pd.DataFrame()
        non_index_symbols: tuple[str, ...] = ()
        extra_symbol_prices: dict[str, float] = {}

        with st.spinner("Fetching KSE-100 data and calculating plan..."):
            kse100 = get_kse100_data()
            if sell_non_kse100:
                kse_symbols = set(
                    kse100["SYMBOL"]
                    .astype(str)
                    .str.replace("XD", "", regex=False)
                    .str.strip()
                    .str.upper()
                )
                portfolio_symbols = set(
                    portfolio_df["SYMBOL"].astype(str).str.strip().str.upper().tolist()
                    if not portfolio_df.empty
                    else []
                )
                non_index_symbols = tuple(sorted(portfolio_symbols - kse_symbols))
                extra_symbol_prices = fetch_latest_psx_prices(non_index_symbols)
                rebalance_plan = build_rebalance_plan(
                    kse100_df=kse100,
                    current_portfolio_df=portfolio_df,
                    target_portfolio_value=money_to_invest,
                    extra_symbol_prices=extra_symbol_prices,
                )
            else:
                investment_plan = compare_current_with_index(
                    kse100=kse100,
                    current_portfolio=portfolio_df,
                    money_to_invest=money_to_invest,
                    threshold=0.0,
                )

        if not sell_non_kse100 and investment_plan.empty:
            st.warning("No stocks matched your criteria for buying at this time.")
        elif not sell_non_kse100:
            investment_plan = investment_plan.sort_values(by="PRICE_TO_INVEST", ascending=False)
            investment_plan.index = investment_plan.index + 1

            st.subheader("Recommended Investment Plan")
            plan_col1, plan_col2 = st.columns(2)
            with plan_col1:
                st.metric("Stocks to Buy", f"{investment_plan['SYMBOL'].nunique()}")
            with plan_col2:
                st.metric("Planned Spend", f"PKR {investment_plan['PRICE_TO_INVEST'].sum():,.0f}")

            st.dataframe(investment_plan, use_container_width=True)
            st.download_button(
                label="Download Investment Plan",
                data=convert_for_download(investment_plan),
                file_name="investment_plan.csv",
                mime="text/csv",
                icon=":material/download:",
                use_container_width=True,
            )
        else:
            st.subheader("Rebalance Portfolio")
            total_symbols = len(non_index_symbols)
            st.caption(
                "KSE-100 symbols use prices from `get_kse100_data`; "
                f"non-index symbols fetched via `get_psx_data`: {len(extra_symbol_prices)}/{total_symbols}. "
                "Fallback pricing used where unavailable."
            )
            net_cash = float(rebalance_plan["TOTAL_COST"].sum())
            rebalance_col1, rebalance_col2, rebalance_col3, rebalance_col4 = st.columns(4)
            with rebalance_col1:
                st.metric("BUY", f"{int((rebalance_plan['ACTION'] == 'BUY').sum())}")
            with rebalance_col2:
                st.metric("SELL", f"{int((rebalance_plan['ACTION'] == 'SELL').sum())}")
            with rebalance_col3:
                st.metric("HOLD", f"{int((rebalance_plan['ACTION'] == 'HOLD').sum())}")
            with rebalance_col4:
                if net_cash > 0:
                    st.metric("Cash Required", f"PKR {net_cash:,.0f}")
                elif net_cash < 0:
                    st.metric("Free Cash", f"PKR {abs(net_cash):,.0f}")
                else:
                    st.metric("Net Cash", "PKR 0")

            styled_rebalance = rebalance_plan.style.apply(color_action_rows, axis=1)
            st.dataframe(styled_rebalance, use_container_width=True, hide_index=True)
            st.download_button(
                label="Download Rebalance Plan",
                data=convert_for_download(rebalance_plan),
                file_name="rebalance_plan.csv",
                mime="text/csv",
                icon=":material/download:",
                use_container_width=True,
            )
