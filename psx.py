import datetime
import tqdm
import argparse
import requests
import pandas as pd
from bs4 import BeautifulSoup

MONTH = datetime.datetime.now().month  # Get the current month
YEAR = datetime.datetime.now().year  # Get the current year


def get_kse100_data():
    """
    Fetches and parses the KSE-100 index data from the Pakistan Stock Exchange website.

    Returns:
        pd.DataFrame: A DataFrame containing the KSE-100 index data with columns as table headers.

    Raises:
        requests.RequestException: If the HTTP request to the PSX website fails.
        AttributeError: If the expected table structure is not found in the HTML.
    """
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
    """
    Fetches PSX (Pakistan Stock Exchange) data for a given symbol, month, and year.

    Args:
        symbol (str): The stock symbol to fetch data for.
        month (str or int, optional): The month for which to fetch data. Defaults to MONTH.
        year (str or int, optional): The year for which to fetch data. Defaults to YEAR.

    Returns:
        dict: A dictionary containing the symbol, date, open, high, low, close, and volume values for the latest entry in the returned data.

    Raises:
        requests.RequestException: If the HTTP request to the PSX data source fails.
        AttributeError: If the expected table structure is not found in the HTML response.
    """
    BASE_URL = "https://dps.psx.com.pk/historical"
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
    """
    Compares the provided symbol with existing data in the DataFrame and returns the total amount already invested in that symbol.
    
    Args:
        df (pandas.DataFrame): The DataFrame containing investment data with columns ["SYMBOL", "SHARE_PRICE", "SHARES", "TOTAL_INVESTED"].
        symbol (str): The symbol to check for existing investment.
    
    Returns:
        float or int: The total amount already invested in the given symbol. Returns 0 if the symbol is not found in the DataFrame.
    """
    # Check how much is already invested in the symbol 
    existing_row = df[ df["SYMBOL"] == symbol ]
    if not len(existing_row):
        return 0
    
    SYMBOL, SHARE_PRICE, SHARES, TOTAL_INVESTED = existing_row.iloc[0]
    return TOTAL_INVESTED


def compare_current_with_index(kse100: pd.DataFrame, 
                               current_portfolio: pd.DataFrame,
                               money_to_invest: float, 
                               threshold: float):
    """
    Compares the current investment portfolio with the KSE-100 index and generates an investment plan
    to align the portfolio with the index's weightages.
    This function:
    - Cleans the KSE-100 DataFrame by removing "XD" from stock symbols.
    - Calculates the amount to invest in each stock based on index weightages and total money to invest.
    - Determines the number of shares to buy for each stock, ensuring at least one share is bought if the stock price is below a specified threshold.
    - Considers existing investments in the current portfolio to avoid over-investing.
    - Returns a DataFrame with the recommended investment plan, including the symbol, amount to invest, current price, and shares to buy.
    Args:
        kse100 (pd.DataFrame): DataFrame containing KSE-100 index data with columns including "SYMBOL", "IDX WTG (%)", and "CURRENT".
        current_portfolio (pd.DataFrame): DataFrame of the current portfolio holdings.
        money_to_invest (float): Total amount of money available to invest.
        threshold (float): Price threshold below which at least one share will be bought if not already invested.
    Returns:
        pd.DataFrame: DataFrame with columns ["SYMBOL", "PRICE_TO_INVEST", "CURRENT_PRICE", "SHARES"] representing the investment plan.
    """
    # cleaning
    kse100["SYMBOL"] = kse100["SYMBOL"].str.replace("XD", "") # remove XD (ex-dividend) from name
    symbols = kse100["SYMBOL"].to_list()
    weightages = kse100["IDX WTG (%)"].tolist()

    # calculate how much to invest in each stock
    money_invested_per_symbol = [money_to_invest * (float(wtg.replace("%", "")) / 100) for wtg in weightages]
    kse100["MONEY INVESTED"] = money_invested_per_symbol
    kse100["SHARES"] = list(map(lambda x: max(x, 1), (kse100["MONEY INVESTED"] / kse100["CURRENT"].str.replace(",", "").astype(float)).round(0)))
    
    # save to disk
    kse100.to_csv(f"kse100_data_month_{MONTH}.csv", index=False)
    
    # Create an investment plan
    header_list = ["SYMBOL", "PRICE_TO_INVEST", "CURRENT_PRICE", "SHARES"]
    rows = []
    for symbol, money_invested in tqdm.tqdm(zip(symbols, money_invested_per_symbol), total=len(symbols)):
        existing_investment = compare_with_existing_data(current_portfolio, symbol)
        row = kse100[ kse100["SYMBOL"] == symbol ]
        
        if not len(row):
            raise Exception("Not possible since symbols are fetched from kse100-df")
        
        _, _, _, CURRENT, _, _, _, _, _, _, _, MONEY_INVESTED, _ = row.iloc[0]
        CURRENT = float(CURRENT.replace(",", ""))

        # Calculate how much to invest
        MONEY_TO_INVEST_NOW = max(MONEY_INVESTED - existing_investment, 0)
        SHARES_TO_BUY = int( float(MONEY_TO_INVEST_NOW) // CURRENT )
        
        # If you are not invested in a stock
        # And the stock does not have enough weightage to buy 1 share of it in your given budget
        # instead of skipping the stock by suggesting 0
        # you can check whether the stock price is below a certain threshold and buy a single share of it
        if not existing_investment and not SHARES_TO_BUY and CURRENT <= threshold:
            SHARES_TO_BUY = 1

        rows.append({
            "SYMBOL": symbol, 
            "PRICE_TO_INVEST": MONEY_TO_INVEST_NOW, 
            "CURRENT_PRICE": CURRENT, 
            "SHARES": int(SHARES_TO_BUY)
        })
    
    # Compile, sort, and save
    return pd.DataFrame(data=rows, columns=header_list)


# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PSX Investment Script")
    parser.add_argument('--money_to_invest', type=float, required=True, help='Amount of money to invest')
    parser.add_argument('--path_to_current_portfolio', type=str, required=True, help='Path to current portfolio')    
    parser.add_argument('--threshold', type=float, required=False, default=0, help='Threshold beyond which a stock is considered expensive')
    args = parser.parse_args()

    print("Fetching PSX data...")
    kse100 = get_kse100_data()

    # Load current portfolio
    current_portfolio = pd.read_csv(args.path_to_current_portfolio)

    investment_plan = compare_current_with_index(kse100, 
                                                 current_portfolio, 
                                                 args.money_to_invest,
                                                 args.threshold)
    investment_plan.sort_values(by="PRICE_TO_INVEST", ascending=False, inplace=True)
    investment_plan.to_csv("investment_plan.csv", index=None)
