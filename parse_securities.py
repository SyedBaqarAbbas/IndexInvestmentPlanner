from __future__ import annotations

import argparse
from pathlib import Path

from psx_app.portfolio import parse_statement_pdf


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parse a securities statement PDF into CSV outputs.")
    parser.add_argument("--input_pdf", type=str, required=True, help="Path to statement PDF.")
    parser.add_argument(
        "--raw_output",
        type=str,
        default="parsed_securities_rows.csv",
        help="Path to write raw parsed rows CSV.",
    )
    parser.add_argument(
        "--portfolio_output",
        type=str,
        default="current_portfolio.csv",
        help="Path to write normalized portfolio summary CSV.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pdf_path = Path(args.input_pdf)
    if not pdf_path.exists():
        raise FileNotFoundError(f"Input PDF does not exist: {pdf_path}")

    parsed_rows, portfolio = parse_statement_pdf(pdf_path.read_bytes())
    parsed_rows.to_csv(args.raw_output, index=False)
    portfolio.to_csv(args.portfolio_output, index=False)

    print(f"Raw parsed rows saved to: {args.raw_output}")
    print(f"Portfolio summary saved to: {args.portfolio_output}")
    print(f"Rows parsed: {len(parsed_rows)} | Symbols: {portfolio['SYMBOL'].nunique() if not portfolio.empty else 0}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
