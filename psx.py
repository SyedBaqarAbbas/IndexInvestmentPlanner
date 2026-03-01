from __future__ import annotations

import argparse

from psx_app.market import get_kse100_data, get_psx_data
from psx_app.planner import compare_current_with_index
from psx_app.portfolio import load_portfolio_csv

__all__ = ["compare_current_with_index", "get_kse100_data", "get_psx_data", "main"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PSX Investment Planner CLI")
    parser.add_argument(
        "--money_to_invest",
        type=float,
        required=True,
        help="Total amount to allocate against KSE-100 weightages.",
    )
    parser.add_argument(
        "--path_to_current_portfolio",
        type=str,
        required=True,
        help="Path to portfolio CSV.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="Optional per-share threshold to force 1 share for unowned low-price symbols.",
    )
    parser.add_argument(
        "--output_plan",
        type=str,
        default="investment_plan.csv",
        help="Path to save generated investment plan CSV.",
    )
    parser.add_argument(
        "--output_kse100",
        type=str,
        default="",
        help="Optional path to save raw fetched KSE-100 data CSV.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("Fetching KSE-100 data...")
    kse100_df = get_kse100_data()
    if args.output_kse100:
        kse100_df.to_csv(args.output_kse100, index=False)
        print(f"KSE-100 data saved to: {args.output_kse100}")

    print("Loading current portfolio...")
    current_portfolio_df = load_portfolio_csv(args.path_to_current_portfolio)

    print("Building investment plan...")
    investment_plan = compare_current_with_index(
        kse100=kse100_df,
        current_portfolio=current_portfolio_df,
        money_to_invest=args.money_to_invest,
        threshold=args.threshold,
    )
    investment_plan.to_csv(args.output_plan, index=False)
    print(f"Investment plan saved to: {args.output_plan}")
    print(f"Rows generated: {len(investment_plan)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
