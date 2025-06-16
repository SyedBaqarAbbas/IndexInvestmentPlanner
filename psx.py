import datetime
import tqdm
import requests
import pandas as pd
from bs4 import BeautifulSoup

BASE_URL = "https://dps.psx.com.pk/historical"
MONTH = datetime.datetime.now().month  # Get the current month
YEAR = datetime.datetime.now().year  # Get the current year
MONEY_TO_INVEST = 300_000  # Total money to invest

PATH_TO_CURRENT_PORTFOLIO = f"Investments - Current Portfolio.csv"


def get_kse100_data():
    # Fetch KSE-100 index data for the specified month
    kse100 = "https://dps.psx.com.pk/indices/KSE100"
    response = requests.get(kse100)
    soup = BeautifulSoup(response.content, "html.parser")

    # Extract the table header and body
    header = soup.find('thead', {"class": "tbl__head"})
    tr_tags = header.find('tr')
    th_tags = tr_tags.find_all('th')
    header_list = [th.text.strip() for th in th_tags]

    # Extract the table body
    tbody = soup.find('tbody', {"class": "tbl__body"})
    tr_tags = tbody.find_all('tr')
    rows = []
    for tr in tr_tags:
        td_tags = tr.find_all('td')
        row = [td.text.strip() for td in td_tags]
        rows.append(row)

    df = pd.DataFrame(rows, columns=header_list)
    return df


def get_psx_data(symbol, month=MONTH, year=YEAR):
    # Fetch PSX data for a specific symbol for the specified month and year
    data = {
        "month": month,
        "year": year,
        "symbol": symbol
    }
    response = requests.post(BASE_URL, data=data)
    page = response.content
    soup = BeautifulSoup(page, "html.parser")
    tr_tags = soup.find_all('tr')
    DATE, OPEN,	HIGH, LOW, CLOSE, VOLUME = tr_tags[1].find_all('td')  # This will print the first date in the table
    row = {
        "SYMBOL": symbol,
        "DATE": DATE.text, 
        "OPEN": OPEN.text,	
        "HIGH": HIGH.text, 
        "LOW": LOW.text, 
        "CLOSE": CLOSE.text, 
        "VOLUME": VOLUME.text
    }
    return row


def compare_with_existing_data(df, symbol):
    # Check how much is already invested in the symbol 
    existing_row = df[ df["SYMBOL"] == symbol ]
    if not len(existing_row):
        return 0
    
    SYMBOL, SHARE_PRICE, SHARES, TOTAL_INVESTED = existing_row.iloc[0]
    return TOTAL_INVESTED


# Example usage
if __name__ == "__main__":
    print("Fetching PSX data...")
    kse100 = get_kse100_data()

    # cleaning
    kse100["SYMBOL"] = kse100["SYMBOL"].str.replace("XD", "") # remove XD (ex-dividend) from name
    symbols = kse100["SYMBOL"].to_list()
    weightages = kse100["IDX WTG (%)"].tolist()

    # calculate how much to invest in each stock
    money_invested_per_symbol = [MONEY_TO_INVEST * (float(wtg.replace("%", "")) / 100) for wtg in weightages]
    kse100["MONEY INVESTED"] = money_invested_per_symbol
    kse100["SHARES"] = list(map(lambda x: max(x, 1), (kse100["MONEY INVESTED"] / kse100["CURRENT"].str.replace(",", "").astype(float)).round(0)))
    
    # save to disk
    kse100.to_csv(f"kse100_data_month_{MONTH}.csv", index=False)

    # Load current portfolio
    current_portfolio = pd.read_csv(PATH_TO_CURRENT_PORTFOLIO)
    
    # Create an investment plan
    header_list = ["SYMBOL", "PRICE_TO_INVEST", "CURRENT_PRICE", "SHARES"]
    rows = []
    for symbol, money_invested in tqdm.tqdm(zip(symbols, money_invested_per_symbol), total=len(symbols)):
        existing_investment = compare_with_existing_data(current_portfolio, symbol)
        row = kse100[ kse100["SYMBOL"] == symbol ]
        
        if not len(row):
            raise Exception("Not possible since symbols are fetched from kse100-df")
        
        _, _, _, CURRENT, _, _, _, _, _, _, _, MONEY_INVESTED, _ = row.iloc[0]

        # Calculate how much to invest
        MONEY_TO_INVEST_NOW = max(MONEY_INVESTED - existing_investment, 0)
        SHARES_TO_BUY = float(MONEY_TO_INVEST_NOW) // float(CURRENT.replace(",", ""))
        
        # cater for low percentage shares that you don't own yet
        # if money to invest is 0, it means you already own enough shares than needed for index fund
        if MONEY_TO_INVEST_NOW:
            SHARES_TO_BUY += 1
        
        rows.append({
            "SYMBOL": symbol, 
            "PRICE_TO_INVEST": MONEY_TO_INVEST_NOW, 
            "CURRENT_PRICE": CURRENT, 
            "SHARES": int(SHARES_TO_BUY)
        })
    
    # Compile, sort, and save
    investment_plan = pd.DataFrame(data=rows, columns=header_list)
    investment_plan.sort_values(by="PRICE_TO_INVEST", ascending=False, inplace=True)
    investment_plan.to_csv("investment_plan.csv", index=None)
