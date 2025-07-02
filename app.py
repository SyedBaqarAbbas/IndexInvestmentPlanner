import time
import pandas as pd
import streamlit as st
from psx import get_kse100_data, compare_current_with_index

@st.cache_data
def convert_for_download(df):
    return df.to_csv().encode("utf-8")

st.title("KSE-100 Tracker")
money_to_invest = st.number_input("Insert money to invest", min_value=0)
threshold = st.number_input("Insert a threshold (a price beyond which you won't buy a stock)", min_value=0,
                            help="During index investing, sometimes a stock's value in your portfolio would fall below its actual value. For example, for 100k invested, the weightage of MEHT translates to Rs.180 but this is below its share price (300 atm). For these cases, you can set a threshold like 500, that states that if a stock is below 500 buy it only if my current portfolio does not have it and the index percentage makes it fall below its actual price.")
kse_100_fetch_button = st.button("Click to fetch index")
current_portfolio = pd.DataFrame(data={}, columns=["SYMBOL","SHARE PRICE","SHARES","TOTAL INVESTED"])

while not kse_100_fetch_button:
   time.sleep(1)

kse100 = get_kse100_data()

investment_plan = compare_current_with_index(kse100, 
                                            current_portfolio, 
                                            money_to_invest,
                                            threshold)

# Make the index start from 1 instead of 0
investment_plan.index = investment_plan.index + 1
st.table(investment_plan)

st.download_button(
    label="Download Investment Plan",
    data=convert_for_download(investment_plan),
    file_name="investment_plan.csv",
    mime="text/csv",
    icon=":material/download:",
)