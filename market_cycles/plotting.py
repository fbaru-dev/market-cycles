"""
Matplotlib visualisations for the market cycles framework.
"""

import math
import os

import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd


# ==============================================================================
# INTERNAL HELPERS
# ==============================================================================

def _save_figure(save_path: str, filename: str) -> None:
    """Save the current matplotlib figure as PNG and TIFF at 300 dpi."""
    os.makedirs(save_path, exist_ok=True)
    png_path  = os.path.join(save_path, f"{filename}.png")
    tiff_path = os.path.join(save_path, f"{filename}.tiff")
    plt.savefig(png_path,  dpi=300)
    plt.savefig(tiff_path, dpi=300)
    print(f"  Saved PNG : {png_path}")
    print(f"  Saved TIFF: {tiff_path}")


def _classify_cycle(dd: float) -> str:
    dd = abs(dd)
    if dd >= 0.20:   return "bear"
    elif dd >= 0.10: return "correction"
    else:            return "small"


# ==============================================================================
# PRICE CHART WITH CYCLE SHADING
# ==============================================================================

def plot_recovery_cycles(
    prices: pd.Series,
    cycles: pd.DataFrame,
    ticker: str,
    save_path: str = ".",
    filename: str = "recovery_cycles",
    with_flags: bool = True,
    log_scale: bool = True,
) -> None:
    """
    Price chart with drawdown cycles shaded by type.

    Shading spans from peak_date to trough_date (the falling phase only):
      red  = bear market  (drawdown >= 20%)
      blue = correction   (drawdown >= 10% and < 20%)
      no shading = small corrections (< 10%)

    Parameters
    ----------
    prices     : pd.Series with DatetimeIndex and float price values
    cycles     : output of identify_market_cycles()
    ticker     : string label used in the chart title
    save_path  : directory for saved PNG and TIFF files
    filename   : base filename (no extension)
    with_flags : if True, annotate each band with drawdown %, days to
                 trough, and days to recovery
    log_scale  : if True, y-axis uses a logarithmic scale with clean
                 round-number tick marks computed dynamically from the
                 actual price range
    """
    BEAR_COLOR       = "#d62728"
    CORRECTION_COLOR = "#2C7BB6"
    ALPHA            = 0.20

    cycles = cycles.copy()
    cycles["_type"] = cycles["drawdown_pct"].apply(_classify_cycle)

    fig, ax = plt.subplots(figsize=(14, 6))

    if log_scale:
        ax.set_yscale("log")

        p_min = float(prices.min())
        p_max = float(prices.max())

        decade_min = int(math.floor(math.log10(p_min)))
        decade_max = int(math.ceil(math.log10(p_max)))

        ticks = []
        for decade in range(decade_min, decade_max + 1):
            base = 10 ** decade
            for mult in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
                val = base * mult
                if p_min * 0.90 <= val <= p_max * 1.10:
                    ticks.append(val)

        ax.set_yticks(ticks)
        ax.yaxis.set_major_formatter(mticker.ScalarFormatter())
        ax.yaxis.set_minor_locator(mticker.NullLocator())
        ax.yaxis.get_major_formatter().set_scientific(False)
        ax.yaxis.get_major_formatter().set_useOffset(False)

    ax.plot(prices.index, prices.values,
            color="#333333", linewidth=1.5, zorder=3)

    y_min = float(prices.min()) * 0.9
    y_max = float(prices.max()) * 1.1
    ax.set_ylim(y_min, y_max)

    for _, row in cycles.iterrows():
        ctype = row["_type"]
        if ctype == "small":
            continue

        color = BEAR_COLOR if ctype == "bear" else CORRECTION_COLOR

        ax.axvspan(row["peak_date"], row["trough_date"],
                   alpha=ALPHA, color=color, linewidth=0, zorder=1)

        if with_flags:
            mid_date = (row["peak_date"]
                        + (row["trough_date"] - row["peak_date"]) / 2)

            if log_scale:
                y_pos = math.exp(
                    math.log(y_min) + (math.log(y_max) - math.log(y_min)) * 0.12
                )
            else:
                y_pos = y_min + (y_max - y_min) * 0.12

            dd_str  = f"{row['drawdown_pct']:.1%}"
            dur_str = f"({int(row['days_to_trough'])}d)"
            rec_str = (f"{int(row['days_to_recovery'])}d rec"
                       if pd.notna(row["days_to_recovery"]) else "N/A")

            ax.text(mid_date, y_pos,
                    f"{dd_str}\n{dur_str}\n{rec_str}",
                    ha="center", va="bottom",
                    fontsize=7, color=color,
                    fontweight="bold", zorder=5)

    ax.set_title(f"{ticker} -- Drawdown Recovery Cycles",
                 fontsize=14, weight="bold")
    ax.set_ylabel("Price")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.grid(True, axis="y", linestyle="--", alpha=0.4)
    ax.grid(False, axis="x")

    ax.legend(handles=[
        mpatches.Patch(facecolor=BEAR_COLOR,       alpha=0.5,
                       label="Bear Market (>= 20%)"),
        mpatches.Patch(facecolor=CORRECTION_COLOR, alpha=0.5,
                       label="Correction (10% - 20%)"),
    ], loc="upper left", framealpha=0.9)

    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))

    plt.setp(ax.xaxis.get_majorticklabels(), fontsize=9, rotation=0, ha="center")

    ax.grid(True, axis="x", which="major", linestyle="--", alpha=0.3, zorder=0)
    ax.grid(True, axis="x", which="minor", linestyle=":",  alpha=0.15, zorder=0)
    ax.grid(True, axis="y", which="major", linestyle="--", alpha=0.4,  zorder=0)

    plt.tight_layout()
    _save_figure(save_path, filename)
    plt.show()


# ==============================================================================
# DURATION BAR CHART
# ==============================================================================

def plot_cycle_duration_bars(
    cycles: pd.DataFrame,
    ticker: str,
    cycle_type: str = "Bear Market",
    metric: str = "days_to_trough",
    save_path: str = ".",
    filename: str = "cycle_duration_bars",
) -> None:
    """
    Horizontal bar chart showing duration of market cycles.

    Parameters
    ----------
    cycles     : output of identify_market_cycles()
    ticker     : string label used in the chart title
    cycle_type : "Bear Market" or "Correction"
    metric     : "days_to_trough", "days_to_recovery", or "full_cycle_days"
    save_path  : directory for saved files
    filename   : base filename without extension
    """
    df = cycles[cycles["type"] == cycle_type].copy()
    if df.empty:
        print(f"No {cycle_type} events found.")
        return

    df["label"] = df["peak_date"].apply(
        lambda d: f"{d.month}/{d.day}/{d.year}"
        if hasattr(d, "strftime") else str(d)
    )
    df = df.sort_values("peak_date", ascending=True).reset_index(drop=True)

    valid   = df[metric].dropna()
    avg_val = float(valid.mean()) if len(valid) > 0 else None

    avg_row          = pd.DataFrame([{metric: avg_val, "is_avg": True}])
    avg_row["label"] = "Average"
    df["is_avg"]     = False
    plot_df          = pd.concat([df, avg_row], ignore_index=True)

    BLUE  = "#1A5276"
    GREEN = "#2E86C1"
    bar_colors = [GREEN if row["is_avg"] else BLUE
                  for _, row in plot_df.iterrows()]

    metric_labels = {
        "days_to_trough":   "Days (Peak to Trough)",
        "days_to_recovery": "Days (Trough to Recovery)",
        "full_cycle_days":  "Days (Peak to Recovery)",
    }
    metric_label = metric_labels.get(metric, metric)
    type_label   = "Bear Markets" if cycle_type == "Bear Market" else "Corrections"

    n_bars  = len(plot_df)
    fig_h   = max(6, n_bars * 0.55)
    fig, ax = plt.subplots(figsize=(13, fig_h))

    vals   = plot_df[metric].fillna(0).values.astype(float)
    labels = plot_df["label"].values
    y_pos  = np.arange(n_bars)

    ax.barh(y_pos, vals, color=bar_colors,
            edgecolor="white", linewidth=0.4, height=0.7)

    for i, val in enumerate(vals):
        if val == 0 or np.isnan(val):
            continue
        ax.text(val + (vals.max() * 0.01), y_pos[i],
                f"{int(round(val))}",
                va="center", ha="left",
                fontsize=9, fontweight="bold", color="black")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9)

    x_max   = vals.max() * 1.18
    x_step  = 100
    x_ticks = np.arange(0, int(x_max / x_step + 2) * x_step, x_step)

    ax.set_xlim(0, x_max)
    ax.set_xticks(x_ticks)
    ax.xaxis.set_tick_params(labelsize=9)

    ax_top = ax.twiny()
    ax_top.set_xlim(ax.get_xlim())
    ax_top.set_xticks(x_ticks)
    ax_top.xaxis.set_tick_params(labelsize=9)

    ax.set_xlabel(metric_label, fontsize=10, labelpad=8)
    ax.set_axisbelow(True)

    ax.xaxis.set_minor_locator(mticker.MultipleLocator(20))
    ax.grid(True, axis="x", which="minor",
            linestyle=":", alpha=0.3, color="gray")
    ax_top.xaxis.set_minor_locator(mticker.MultipleLocator(20))
    ax.xaxis.grid(True, which="major", linestyle="--", alpha=0.5, color="gray")
    ax.yaxis.grid(False)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    ax.set_title(
        f"History of Length of {ticker} {type_label}\n{metric_label}",
        fontsize=13, fontweight="bold",
        color="black", loc="center", pad=14,
    )

    ax.invert_yaxis()
    plt.tight_layout()
    _save_figure(save_path, filename)
    plt.show()


# ==============================================================================
# DRAWDOWN BAR CHART
# ==============================================================================

def plot_cycle_drawdown_bars(
    cycles: pd.DataFrame,
    ticker: str,
    cycle_type: str = "Bear Market",
    save_path: str = ".",
    filename: str = "cycle_drawdown_bars",
) -> None:
    """
    Horizontal bar chart showing drawdown percentage for each market cycle.

    Parameters
    ----------
    cycles     : output of identify_market_cycles()
    ticker     : string label used in the chart title
    cycle_type : "Bear Market" or "Correction"
    save_path  : directory for saved files
    filename   : base filename without extension
    """
    df = cycles[cycles["type"] == cycle_type].copy()
    if df.empty:
        print(f"No {cycle_type} events found.")
        return

    df["label"] = df["peak_date"].apply(
        lambda d: f"{d.month}/{d.day}/{d.year}"
        if hasattr(d, "strftime") else str(d)
    )
    df = df.sort_values("peak_date", ascending=True).reset_index(drop=True)

    avg_val          = float(df["drawdown_pct"].mean())
    avg_row          = pd.DataFrame([{"drawdown_pct": avg_val, "is_avg": True}])
    avg_row["label"] = "Average"
    df["is_avg"]     = False
    plot_df          = pd.concat([df, avg_row], ignore_index=True)

    BLUE  = "#1A5276"
    GREEN = "#2E86C1"
    bar_colors = [GREEN if row["is_avg"] else BLUE
                  for _, row in plot_df.iterrows()]

    type_label = "Bear Markets" if cycle_type == "Bear Market" else "Corrections"

    n_bars  = len(plot_df)
    fig_h   = max(6, n_bars * 0.55)
    fig, ax = plt.subplots(figsize=(13, fig_h))

    vals   = plot_df["drawdown_pct"].fillna(0).values.astype(float)
    labels = plot_df["label"].values
    y_pos  = np.arange(n_bars)

    ax.barh(y_pos, vals, color=bar_colors,
            edgecolor="white", linewidth=0.4, height=0.7)

    for i, val in enumerate(vals):
        if val == 0 or np.isnan(val):
            continue
        ax.text(val - (abs(vals.min()) * 0.01), y_pos[i],
                f"{val*100:.1f}%",
                va="center", ha="right",
                fontsize=9, fontweight="bold", color="black")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9)

    x_min   = vals.min() * 1.15
    x_step  = 0.05
    x_ticks = np.arange(0, x_min - x_step, -x_step)[::-1]

    ax.set_xlim(x_min, 0)
    ax.set_xticks(x_ticks)
    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"{x*100:.0f}%")
    )
    ax.xaxis.set_tick_params(labelsize=9)

    ax.xaxis.set_minor_locator(mticker.MultipleLocator(0.01))
    ax.grid(True, axis="x", which="major",
            linestyle="--", alpha=0.5, color="gray", zorder=0)
    ax.grid(True, axis="x", which="minor",
            linestyle=":",  alpha=0.3, color="gray", zorder=0)
    ax.yaxis.grid(False)

    ax_top = ax.twiny()
    ax_top.set_xlim(ax.get_xlim())
    ax_top.set_xticks(x_ticks)
    ax_top.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"{x*100:.0f}%")
    )
    ax_top.xaxis.set_tick_params(labelsize=9)
    ax_top.xaxis.set_minor_locator(mticker.MultipleLocator(0.01))

    ax.set_xlabel("Drawdown (%)", fontsize=10, labelpad=8)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    ax.set_title(
        f"History of Percent Changes in {ticker} {type_label}",
        fontsize=13, fontweight="bold",
        color="black", loc="center", pad=14,
    )

    ax.invert_yaxis()
    ax.axvline(x=0, color="black", linewidth=0.8)

    plt.tight_layout()
    _save_figure(save_path, filename)
    plt.show()
