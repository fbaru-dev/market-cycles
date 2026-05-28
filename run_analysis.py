"""
Full market cycles analysis pipeline.

Edit market_cycles/config.py to change ticker, dates, and output directory.
Run with:  python run_analysis.py
"""

from market_cycles.config import TICKER, START_DATE, END_DATE, OUTPUT_DIR
from market_cycles import (
    download_price_data,
    identify_market_cycles,
    summarize_recovery_cycles,
    identify_bull_markets,
    summarize_bull_markets,
    plot_recovery_cycles,
    plot_cycle_duration_bars,
    plot_cycle_drawdown_bars,
    print_cycles_table,
)


def main():

    # ── A. DATA ────────────────────────────────────────────────────────────────
    print(f"\nDownloading {TICKER} from {START_DATE} to {END_DATE}...")
    price_df = download_price_data(TICKER, START_DATE, END_DATE)
    prices   = price_df["price"]
    print(f"  {len(prices)} trading days loaded.\n")

    # ── B. CYCLE DETECTION ────────────────────────────────────────────────────
    print("B. Identifying bear markets and corrections...")
    cycles = identify_market_cycles(prices)
    print(f"  {len(cycles)} events identified.\n")

    # ── C. TEXT SUMMARY ───────────────────────────────────────────────────────
    print("C. Summary of recovery cycles...")
    summarize_recovery_cycles(cycles, top_n=None)

    # ── D. RICH TABLE ─────────────────────────────────────────────────────────
    print("D. Rich table...")
    print_cycles_table(cycles)

    # ── E. BULL MARKETS ───────────────────────────────────────────────────────
    print("E. Identifying bull markets...")
    bulls = identify_bull_markets(cycles, prices)
    summarize_bull_markets(bulls)

    # ── F. PRICE CHART WITH CYCLE SHADING ─────────────────────────────────────
    print("F. Price chart with cycle shading...")
    plot_recovery_cycles(
        prices, cycles, ticker=TICKER,
        save_path=OUTPUT_DIR, filename="recovery_cycles",
    )

    # ── G. BEAR MARKET CHARTS ─────────────────────────────────────────────────
    print("G. Bear market bar charts...")
    plot_cycle_duration_bars(
        cycles, ticker=TICKER, cycle_type="Bear Market",
        metric="days_to_trough",
        save_path=OUTPUT_DIR, filename="bear_duration_bars",
    )
    plot_cycle_drawdown_bars(
        cycles, ticker=TICKER, cycle_type="Bear Market",
        save_path=OUTPUT_DIR, filename="bear_drawdown_bars",
    )

    # ── H. CORRECTION CHARTS ──────────────────────────────────────────────────
    print("H. Correction bar charts...")
    plot_cycle_duration_bars(
        cycles, ticker=TICKER, cycle_type="Correction",
        metric="days_to_trough",
        save_path=OUTPUT_DIR, filename="correction_duration_bars",
    )
    plot_cycle_drawdown_bars(
        cycles, ticker=TICKER, cycle_type="Correction",
        save_path=OUTPUT_DIR, filename="correction_drawdown_bars",
    )

    print("\nAll analyses complete.")


if __name__ == "__main__":
    main()
