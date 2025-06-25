# KSE-100 Portfolio Investment Planner

## Overview

This tool helps you plan your investments in the KSE-100 index. It calculates how much you need to invest in each company based on the index weightage, taking into account your current portfolio and your total investment goal.

## How to Use

### 1. Install Requirements

Make sure you have Python 3 installed.  
Install the required packages using:

```sh
pip install -r requirements.txt
```

## 2. Prepare Your Current Portfolio

Create or update your portfolio CSV file (e.g., `Investments - Current Portfolio.csv`) in the following format:

```
SYMBOL,SHARE_PRICE,SHARES,TOTAL_INVESTED
FFC,357.02,65,23206.3
...
```

## 3. Run the Script

Use the command line to run the script with the required arguments:

```sh
python psx.py --money_to_invest <TOTAL_AMOUNT> --path_to_current_portfolio "<PORTFOLIO_CSV_PATH>"
```

- `<TOTAL_AMOUNT>`: The total amount you want to have invested (e.g., 300000).
- `<PORTFOLIO_CSV_PATH>`: Path to your current portfolio CSV file.

**Optional:**  
You can also specify a `--threshold` value to define the maximum price for buying a single share of an otherwise underweight stock:

```sh
python psx.py --money_to_invest 300000 --path_to_current_portfolio "Investments - Current Portfolio.csv" --threshold 100
```


## Output

- **KSE100.csv**  
  Contains the current KSE-100 weightage, the amount to invest in each company, and the number of shares to buy.

- **INVESTMENT_PLAN**  
  Shows the following columns: `SYMBOL`, `PRICE_TO_INVEST`, `CURRENT_PRICE`, and `SHARES` to buy.

---