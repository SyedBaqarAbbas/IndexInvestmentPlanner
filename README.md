# KSE-100 Portfolio Investment Planner

View the app here: [KSE-100 Index Investment Planner](https://kse100index.streamlit.app/)

## Overview

This project helps you align a portfolio with KSE-100 index weights. It supports:

- Portfolio upload via CSV
- Securities statement PDF parsing
- Buy-only recommendations
- Full rebalance plans (buy/sell/hold)

## Project Structure

Core business logic lives in `psx_app/`:

- `psx_app/market.py`: PSX/KSE network fetching and parsing
- `psx_app/planner.py`: investment and rebalance calculations
- `psx_app/portfolio.py`: shared portfolio/PDF/CSV helpers

UI files (`app.py`, `pages/*.py`) are intentionally thin and call shared services.

## Setup

```sh
pip install -r requirements.txt
```

## Run Streamlit App

```sh
streamlit run app.py
```

## CLI Usage

Generate investment plan from an existing CSV portfolio:

```sh
python psx.py --money_to_invest 300000 --path_to_current_portfolio "Investments - Current Portfolio.csv"
```

Optional arguments:

- `--threshold 100`: force one share for unowned symbols priced under threshold
- `--output_plan investment_plan.csv`: output CSV path
- `--output_kse100 kse100.csv`: optional raw KSE-100 snapshot output

Parse a securities statement PDF directly:

```sh
python parse_securities.py --input_pdf statement.pdf
```

Optional arguments:

- `--raw_output parsed_securities_rows.csv`
- `--portfolio_output current_portfolio.csv`
