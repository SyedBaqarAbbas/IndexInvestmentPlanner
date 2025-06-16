# KSE-100 Portfolio Investment Planner

## Overview

This tool helps you plan your investments in the KSE-100 index. It calculates how much you need to invest in each company based on the index weightage, taking into account your current portfolio and your total investment goal.

## How to Use

1. **Provide Your Current Portfolio**

   List your current holdings in the following format:

   ```
   SYMBOL,SHARE PRICE,SHARES,TOTAL INVESTED
   MIIETF,12.97,2500,32425
   FFC,357.02,65,23206.3
   ```

2. **Set Your Total Investment (`MONEY_TO_INVEST`)**

   Specify the total amount you want to have invested in the KSE-100, including your current holdings.

   *Example:*  
   If you want your total KSE-100 investment to be 300,000, the tool will calculate the required investment in each company according to its weightage, subtract your existing investments, and generate a plan showing how many additional shares you need to buy.

## Output

- **KSE100.csv**  
  Contains the current KSE-100 weightage, the amount to invest in each company, and the number of shares to buy.

- **INVESTMENT_PLAN**  
  Shows the following columns: `SYMBOL`, `PRICE_TO_INVEST`, `CURRENT_PRICE`, and `SHARES` to buy.

---