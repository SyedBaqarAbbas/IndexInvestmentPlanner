import pandas as pd
import streamlit as st

from securities_parser import parse_securities_pdf_bytes, portfolio_from_parsed_rows

st.set_page_config(page_title="Portfolio Parser", page_icon=":page_facing_up:", layout="wide")


@st.cache_data
def convert_for_download(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


@st.cache_data(show_spinner=False)
def parse_document(pdf_bytes: bytes) -> tuple[pd.DataFrame, pd.DataFrame]:
    parsed_df = parse_securities_pdf_bytes(pdf_bytes)
    portfolio_df = portfolio_from_parsed_rows(parsed_df)
    return parsed_df, portfolio_df


st.markdown(
    """
    <style>
      .block-container {
          padding-top: 1.2rem;
          padding-bottom: 2rem;
      }
      .header-card {
          border: 1px solid rgba(127, 127, 127, 0.28);
          border-radius: 16px;
          padding: 1rem 1.2rem;
          background: linear-gradient(
            120deg,
            var(--secondary-background-color) 0%,
            var(--background-color) 100%
          );
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
    <div class="header-card">
      <h2 style="margin:0 0 0.25rem 0;">Securities Statement Parser</h2>
      <p style="margin:0;">
        Upload your PDF statement and export normalized portfolio data for the planner.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_pdf = st.file_uploader("Upload securities statement (.pdf)", type=["pdf"])

if uploaded_pdf is None:
    st.info("Upload a PDF to begin parsing.")
else:
    try:
        parsed_rows, portfolio = parse_document(uploaded_pdf.getvalue())
    except Exception as exc:
        st.error(f"Unable to parse the statement: {exc}")
    else:
        if parsed_rows.empty:
            st.warning("No matching securities records were found in this file.")
        else:
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            with metric_col1:
                st.metric("Rows Parsed", f"{len(parsed_rows):,}")
            with metric_col2:
                st.metric("Symbols", f"{portfolio['SYMBOL'].nunique():,}")
            with metric_col3:
                st.metric("Total Invested", f"PKR {portfolio['TOTAL INVESTED'].sum():,.0f}")

            tab1, tab2 = st.tabs(["Portfolio Summary", "Raw Parsed Rows"])

            with tab1:
                st.dataframe(portfolio, use_container_width=True, hide_index=True)
                st.download_button(
                    label="Download Portfolio CSV",
                    data=convert_for_download(portfolio),
                    file_name="current_portfolio.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            with tab2:
                st.dataframe(parsed_rows, use_container_width=True, hide_index=True)
                st.download_button(
                    label="Download Raw Parsed Rows",
                    data=convert_for_download(parsed_rows),
                    file_name="parsed_securities_rows.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
