"""
Bear market and correction cycle detection and summarisation.
"""

import numpy as np
import pandas as pd

from .config import CORRECTION_THRESHOLD, BEAR_THRESHOLD


def identify_market_cycles(
    prices: pd.Series,
    correction_threshold: float = None,
    bear_threshold: float = None,
) -> pd.DataFrame:
    """
    Identify corrections and bear markets from a price series.

    Returns one clean row per distinct market event with zero overlaps.
    See README for the full five-step algorithm description.

    Parameters
    ----------
    prices               : pd.Series with DatetimeIndex and float values
    correction_threshold : minimum decline to record as an event.
                           Defaults to config.CORRECTION_THRESHOLD (5%).
    bear_threshold       : minimum decline to label as a bear market.
                           Defaults to config.BEAR_THRESHOLD (20%).

    Returns
    -------
    pd.DataFrame with columns:
        type, peak_date, peak_price, trough_date, trough_price,
        recovery_date, drawdown_pct, days_to_trough, days_to_recovery,
        full_cycle_days, recovered
    """
    if correction_threshold is None:
        correction_threshold = CORRECTION_THRESHOLD
    if bear_threshold is None:
        bear_threshold = BEAR_THRESHOLD

    # ------------------------------------------------------------------
    # Step 1: rolling drawdown
    # ------------------------------------------------------------------
    rolling_peak = prices.rolling(window=252, min_periods=1).max()
    drawdown     = (prices - rolling_peak) / rolling_peak
    below        = (drawdown <= -correction_threshold).values
    price_vals   = prices.values.astype(float)
    peak_vals    = rolling_peak.values.astype(float)
    dates        = prices.index
    n            = len(prices)

    # ------------------------------------------------------------------
    # Step 2: contiguous block detection
    # ------------------------------------------------------------------
    raw_cycles = []
    i          = 0

    while i < n:
        if not below[i]:
            i += 1
            continue

        block_start = i

        j = i + 1
        while j < n and below[j]:
            j += 1
        block_end = j - 1

        peak_price = float(peak_vals[block_start])

        peak_date = dates[block_start]
        for k in range(block_start, -1, -1):
            if price_vals[k] >= peak_price:
                peak_date = dates[k]
                break

        block_slice  = price_vals[block_start : block_end + 1]
        trough_pos   = int(np.argmin(block_slice))
        trough_price = float(block_slice[trough_pos])
        trough_date  = dates[block_start + trough_pos]
        dd_pct       = (trough_price - peak_price) / peak_price

        recovery_date    = pd.NaT
        days_to_recovery = np.nan
        full_cycle_days  = (dates[-1] - peak_date).days
        recovered        = False

        for k in range(block_end + 1, n):
            if price_vals[k] >= peak_price:
                recovery_date    = dates[k]
                days_to_recovery = (recovery_date - trough_date).days
                full_cycle_days  = (recovery_date - peak_date).days
                recovered        = True
                break

        raw_cycles.append({
            "type":             "Bear Market" if dd_pct <= -bear_threshold
                                else "Correction",
            "peak_date":        peak_date,
            "peak_price":       peak_price,
            "trough_date":      trough_date,
            "trough_price":     trough_price,
            "recovery_date":    recovery_date,
            "drawdown_pct":     dd_pct,
            "days_to_trough":   (trough_date - peak_date).days,
            "days_to_recovery": days_to_recovery,
            "full_cycle_days":  full_cycle_days,
            "recovered":        recovered,
        })

        i = block_end + 1

    if not raw_cycles:
        return pd.DataFrame()

    df = pd.DataFrame(raw_cycles)

    # ------------------------------------------------------------------
    # Step 3: one row per peak_date — keep worst drawdown
    # ------------------------------------------------------------------
    df = (df.sort_values("drawdown_pct")
            .drop_duplicates(subset="peak_date", keep="first")
            .sort_values("peak_date")
            .reset_index(drop=True))

    # ------------------------------------------------------------------
    # Step 4: one row per trough cluster — keep worst drawdown
    # ------------------------------------------------------------------
    df_sorted    = df.sort_values("drawdown_pct").reset_index(drop=True)
    kept         = []
    used_troughs = []

    for _, row in df_sorted.iterrows():
        trough = row["trough_date"]
        is_dup = any(abs((trough - u).days) <= 45 for u in used_troughs)
        if not is_dup:
            kept.append(row)
            used_troughs.append(trough)

    if not kept:
        return pd.DataFrame()

    df = (pd.DataFrame(kept)
            .sort_values("peak_date")
            .reset_index(drop=True))

    # ------------------------------------------------------------------
    # Step 5: remove corrections nested inside bear markets
    # ------------------------------------------------------------------
    bears       = df[df["type"] == "Bear Market"]
    corrections = df[df["type"] == "Correction"]

    bear_ranges = [(r["peak_date"], r["trough_date"])
                   for _, r in bears.iterrows()]

    def inside_bear(peak_date):
        for b_start, b_end in bear_ranges:
            if b_start <= peak_date <= b_end:
                return True
        return False

    corrections_clean = corrections[
        ~corrections["peak_date"].apply(inside_bear)
    ]

    return (pd.concat([bears, corrections_clean])
              .sort_values("peak_date")
              .reset_index(drop=True))


def summarize_recovery_cycles(cycles: pd.DataFrame, top_n: int = None) -> None:
    """
    Print a structured plain-text summary of drawdown cycles.

    Parameters
    ----------
    cycles : output of identify_market_cycles()
    top_n  : number of worst drawdowns to show in the table.
             If None, all cycles are shown.
    """
    if len(cycles) == 0:
        print("No drawdown cycles found.")
        return

    def classify(dd: float) -> str:
        dd = abs(dd)
        if dd >= 0.20:   return "Bear Market"
        elif dd >= 0.10: return "Correction"
        else:            return "Small Correction"

    cycles = cycles.copy()
    cycles["market_type"] = cycles["drawdown_pct"].apply(classify)

    total     = len(cycles)
    recovered = int(cycles["recovered"].sum())
    ongoing   = total - recovered
    type_counts = cycles["market_type"].value_counts()

    print("=" * 65)
    print("DRAWDOWN CYCLE SUMMARY")
    print("=" * 65)
    print(f"  Total cycles identified : {total}")
    print(f"  Recovered               : {recovered}  ({recovered/total:.0%})")
    print(f"  Still unrecovered       : {ongoing}")
    print()
    print("  Breakdown by type:")
    for label in ["Bear Market", "Correction", "Small Correction"]:
        count = type_counts.get(label, 0)
        print(f"    {label:<18}: {count}")
    print()

    rec = cycles[cycles["recovered"]]
    if len(rec) > 0:
        print("  Duration statistics (recovered cycles only):")
        print()
        for label in ["Bear Market", "Correction", "Small Correction"]:
            subset = rec[rec["market_type"] == label]
            if len(subset) == 0:
                continue
            print(f"  [{label}]  n={len(subset)}")
            stats = subset[["days_to_trough", "days_to_recovery",
                             "full_cycle_days", "drawdown_pct"]].describe().round(1)
            print(stats.to_string())
            print()

    n_to_show = top_n if top_n is not None else total
    print(f"  {'All' if top_n is None else f'Top {top_n}'} worst drawdowns:")
    print()

    display = cycles.nsmallest(n_to_show, "drawdown_pct")[
        ["market_type", "peak_date", "trough_date", "recovery_date",
         "drawdown_pct", "days_to_trough", "days_to_recovery",
         "full_cycle_days", "recovered"]
    ].copy()

    display["drawdown_pct"]     = display["drawdown_pct"].map("{:.1%}".format)
    display["days_to_trough"]   = display["days_to_trough"].astype(int)
    display["full_cycle_days"]  = display["full_cycle_days"].astype(int)
    display["days_to_recovery"] = display["days_to_recovery"].apply(
        lambda x: str(int(x)) if pd.notna(x) else "N/A"
    )
    display["recovery_date"] = display["recovery_date"].apply(
        lambda x: str(x.date()) if pd.notna(x) else "N/A"
    )
    display["peak_date"]   = display["peak_date"].apply(lambda x: str(x.date()))
    display["trough_date"] = display["trough_date"].apply(lambda x: str(x.date()))

    display.columns = ["Type", "Peak", "Trough", "Recovery",
                       "DD%", "Days to Trough",
                       "Days to Recovery", "Full Cycle", "Recovered"]

    print(display.to_string(index=False))
    print()
