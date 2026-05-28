"""
Bull market identification and summarisation.

A bull market is defined as a period of 20%+ gains starting from a bear
market trough and ending at the next bear market peak (or the end of data
for the current ongoing bull market).
"""

import pandas as pd

from .config import BULL_THRESHOLD


def identify_bull_markets(
    cycles: pd.DataFrame,
    prices: pd.Series,
    bull_threshold: float = None,
) -> pd.DataFrame:
    """
    Identify bull markets as periods of 20%+ gains from bear market troughs.

    A bull market starts at a bear market trough and ends at the next bear
    market peak, provided the total gain exceeds bull_threshold. Periods
    where the gain is below the threshold are not counted — they are
    simply recoveries.

    The current ongoing bull market (last bear trough to end of data)
    is included if its gain also exceeds the threshold.

    Parameters
    ----------
    cycles         : output of identify_market_cycles()
    prices         : full price Series with DatetimeIndex
    bull_threshold : minimum gain to qualify as a bull market.
                     Defaults to config.BULL_THRESHOLD (20%).

    Returns
    -------
    pd.DataFrame with columns:
        start_date, end_date, start_price, end_price,
        gain_pct, duration_days, ongoing
    """
    if bull_threshold is None:
        bull_threshold = BULL_THRESHOLD

    bears = (cycles[cycles["type"] == "Bear Market"]
             .sort_values("peak_date")
             .reset_index(drop=True))

    if len(bears) == 0:
        print("No bear markets found.")
        return pd.DataFrame()

    bulls = []

    for i in range(len(bears) - 1):
        current_bear = bears.iloc[i]
        next_bear    = bears.iloc[i + 1]

        start_date  = current_bear["trough_date"]
        end_date    = next_bear["peak_date"]
        start_price = float(prices.loc[start_date])
        end_price   = float(prices.loc[end_date])
        gain_pct    = (end_price - start_price) / start_price

        if gain_pct < bull_threshold:
            continue

        bulls.append({
            "start_date":    start_date,
            "end_date":      end_date,
            "start_price":   round(start_price, 2),
            "end_price":     round(end_price, 2),
            "gain_pct":      gain_pct,
            "duration_days": (end_date - start_date).days,
            "ongoing":       False,
        })

    # Current ongoing bull market
    last_bear   = bears.iloc[-1]
    start_date  = last_bear["trough_date"]
    end_date    = prices.index[-1]
    start_price = float(prices.loc[start_date])
    end_price   = float(prices.iloc[-1])
    gain_pct    = (end_price - start_price) / start_price

    if gain_pct >= bull_threshold:
        bulls.append({
            "start_date":    start_date,
            "end_date":      end_date,
            "start_price":   round(start_price, 2),
            "end_price":     round(end_price, 2),
            "gain_pct":      gain_pct,
            "duration_days": (end_date - start_date).days,
            "ongoing":       True,
        })

    if not bulls:
        print(f"No bull markets found with gain >= {bull_threshold:.0%}.")
        return pd.DataFrame()

    return pd.DataFrame(bulls).reset_index(drop=True)


def summarize_bull_markets(bulls: pd.DataFrame) -> None:
    """
    Print a structured plain-text summary of bull market periods.

    Parameters
    ----------
    bulls : output of identify_bull_markets()
    """
    if len(bulls) == 0:
        print("No bull markets found.")
        return

    total    = len(bulls)
    avg_gain = bulls["gain_pct"].mean()
    avg_dur  = bulls["duration_days"].mean()
    best     = bulls.loc[bulls["gain_pct"].idxmax()]
    longest  = bulls.loc[bulls["duration_days"].idxmax()]

    print("=" * 70)
    print("BULL MARKET SUMMARY")
    print("=" * 70)
    print(f"  Total bull markets identified : {total}")
    print(f"  Average gain                  : {avg_gain:.1%}")
    print(f"  Average duration              : {avg_dur:.0f} days"
          f"  ({avg_dur/365:.1f} years)")
    print(f"  Best gain                     : {best['gain_pct']:.1%}"
          f"  ({best['start_date'].date()} - {best['end_date'].date()})")
    print(f"  Longest                       : {longest['duration_days']} days"
          f"  ({longest['start_date'].date()} - {longest['end_date'].date()})")
    print()

    col_w  = [12, 12, 10, 10, 10, 14]
    header = (f"{'Start':>{col_w[0]}}  "
              f"{'End':>{col_w[1]}}  "
              f"{'Start ':>{col_w[2]}}  "
              f"{'End ':>{col_w[3]}}  "
              f"{'Gain %':>{col_w[4]}}  "
              f"{'Days':>{col_w[5]}}")
    print(header)
    print("-" * 70)

    for _, row in bulls.sort_values("start_date").iterrows():
        print(
            f"{str(row['start_date'].date()):>{col_w[0]}}  "
            f"{str(row['end_date'].date()):>{col_w[1]}}  "
            f"{row['start_price']:>{col_w[2]}.2f}  "
            f"{row['end_price']:>{col_w[3]}.2f}  "
            f"{row['gain_pct']:>{col_w[4]}.1%}  "
            f"{int(row['duration_days']):>{col_w[5]}}"
        )

    print("-" * 70)
    print(
        f"{'Average':>{col_w[0]}}  "
        f"{'':>{col_w[1]}}  "
        f"{'':>{col_w[2]}}  "
        f"{'':>{col_w[3]}}  "
        f"{avg_gain:>{col_w[4]}.1%}  "
        f"{avg_dur:>{col_w[5]}.0f}"
    )
    print()
