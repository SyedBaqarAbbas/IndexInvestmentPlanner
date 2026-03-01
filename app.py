import pandas as pd
import streamlit as st

from psx import compare_current_with_index, get_kse100_data
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
    st.subheader("Current Portfolio Preview")
    if portfolio_df.empty:
        st.caption("No portfolio loaded yet.")
    else:
        st.dataframe(portfolio_df, use_container_width=True, hide_index=True)

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
        with st.spinner("Fetching KSE-100 data and calculating plan..."):
            kse100 = get_kse100_data()
            investment_plan = compare_current_with_index(
                kse100=kse100,
                current_portfolio=portfolio_df,
                money_to_invest=money_to_invest,
                threshold=0.0,
            )

        if investment_plan.empty:
            st.warning("No stocks matched your criteria for buying at this time.")
        else:
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
