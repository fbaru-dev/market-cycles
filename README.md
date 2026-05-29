# Market Cycles Analysis Framework
## [Fabio Baruffa](https://fabiobaruffa.com) — The Quantitative Edge
A framework for identifying, classifying, and visualising bear markets, corrections, and bull markets from historical price data.

[![Blog](https://img.shields.io/badge/Blog-The%20Quantitative%20Edge-185FA5)](https://fabiobaruffa.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
---

## Motivation

Standard drawdown metrics tell you the worst single decline an asset has ever experienced. This framework goes further: it finds every distinct market cycle in a price history, classifies each one by severity, measures how long each decline and recovery took, and produces publication-quality charts and tables — giving a complete empirical record of how the asset has behaved across all market regimes.

---

## Framework Overview

The analysis proceeds in three conceptual stages:

| Stage | Function | Output |
|-------|----------|--------|
| **Cycle detection** | `identify_market_cycles()` | One clean row per bear market or correction, no overlaps |
| **Bull market identification** | `identify_bull_markets()` | One row per sustained 20%+ advance from a bear trough |
| **Reporting & visualisation** | `summarize_*`, `print_cycles_table`, `plot_*` | Console summaries, Rich tables, PNG/TIFF charts |

---

## Cycle Detection Algorithm

`identify_market_cycles()` runs five steps to produce a clean, non-overlapping event table.

### Step 1 — Rolling drawdown
Compute a 252-day rolling peak and the percentage drawdown from it. Using a rolling (not all-time) peak allows corrections that occur during a bear market recovery to be captured as separate events.

### Step 2 — Contiguous block detection
Find contiguous periods where `drawdown ≤ -correction_threshold`. Each block is processed independently — blocks are non-overlapping by construction. For each block, extract:
- **peak_date**: last date before the block where price was at the rolling peak level
- **trough_date**: worst price inside the block
- **recovery_date**: first date after the block where price returns to the peak level

### Step 3 — Deduplication by peak date
Multiple blocks may share the same `peak_date` when the rolling window creates slightly different reference levels. Keep only the worst drawdown per unique `peak_date`.

### Step 4 — Deduplication by trough cluster
Two events with troughs within 45 days are treated as the same event. Keep only the worst one.

### Step 5 — Remove corrections nested inside bear markets
Any correction whose `peak_date` falls inside a bear market's peak-to-trough date range is removed. Bear markets already represent that period and corrections should not overlap them.

---

## Output Schema

### `identify_market_cycles()` returns a DataFrame with:

| Column | Type | Description |
|--------|------|-------------|
| `type` | str | `"Bear Market"` or `"Correction"` |
| `peak_date` | Timestamp | Date of the local high before the decline |
| `peak_price` | float | Price at peak |
| `trough_date` | Timestamp | Date of the worst price in the event |
| `trough_price` | float | Price at trough |
| `recovery_date` | Timestamp / NaT | First date price returned to peak; NaT if still open |
| `drawdown_pct` | float | `(trough − peak) / peak`, negative fraction |
| `days_to_trough` | int | Calendar days from peak to trough |
| `days_to_recovery` | float / nan | Calendar days from trough to recovery |
| `full_cycle_days` | int | Calendar days from peak to recovery (days to end of data if unrecovered) |
| `recovered` | bool | `True` if price returned to peak within the data |

### `identify_bull_markets()` returns a DataFrame with:

| Column | Type | Description |
|--------|------|-------------|
| `start_date` | Timestamp | Bear market trough date |
| `end_date` | Timestamp | Next bear market peak date (or last data date if ongoing) |
| `start_price` | float | Price at bull start |
| `end_price` | float | Price at bull end |
| `gain_pct` | float | Total gain over the bull market |
| `duration_days` | int | Calendar days of the bull market |
| `ongoing` | bool | `True` if the bull market extends to the end of the data |

---

## Event Classification

| Threshold | Label |
|-----------|-------|
| Drawdown ≥ 20% | Bear Market |
| 10% ≤ Drawdown < 20% | Correction |
| 5% ≤ Drawdown < 10% | Small Correction *(detected but not shaded on charts)* |

---

## Installation

```bash
git clone https://github.com/fbaru-dev/market-cycles.git
cd market-cycles
pip install -r requirements.txt
```

The `print_cycles_table()` function requires the optional `rich` library:

```bash
pip install rich
```

---

## Quick Start

```bash
# Run the full analysis with default settings (SPY, 1996–2026)
python run_analysis.py
```

Edit `market_cycles/config.py` to change the ticker, date range, or output directory.

---

## Usage as a Library

```python
from market_cycles.data   import download_price_data
from market_cycles.cycles import identify_market_cycles, summarize_recovery_cycles
from market_cycles.bulls  import identify_bull_markets, summarize_bull_markets
from market_cycles.plotting import plot_recovery_cycles

# Download data
prices = download_price_data("QQQ", "2000-01-01", "2026-01-01")

# Detect bear markets and corrections
cycles = identify_market_cycles(prices["price"])

# Print summary
summarize_recovery_cycles(cycles, top_n=10)

# Detect and summarise bull markets
bulls = identify_bull_markets(cycles, prices["price"])
summarize_bull_markets(bulls)

# Charts
plot_recovery_cycles(prices["price"], cycles, ticker="QQQ")
```

---

## Output Files

All figures are saved as `.png` and `.tiff` at 300 dpi to `OUTPUT_DIR` (default: current directory).

| Filename | Description |
|----------|-------------|
| `recovery_cycles` | Price chart with bear/correction bands shaded |
| `bear_duration_bars` | Horizontal bars: duration of each bear market |
| `bear_drawdown_bars` | Horizontal bars: drawdown % of each bear market |
| `correction_duration_bars` | Horizontal bars: duration of each correction |
| `correction_drawdown_bars` | Horizontal bars: drawdown % of each correction |

---

## Project Structure

```
market-cycles/
├── README.md
├── requirements.txt
├── run_analysis.py              # Entry point — runs the full pipeline
└── market_cycles/
    ├── __init__.py              # Public API exports
    ├── config.py                # Ticker, dates, output directory
    ├── data.py                  # Yahoo Finance download
    ├── cycles.py                # Bear/correction detection and text summary
    ├── bulls.py                 # Bull market identification and text summary
    ├── plotting.py              # All matplotlib visualisations
    └── reporting.py             # Rich console table (optional dependency)
```

---

## Design Notes

### Why a 252-day rolling peak instead of an all-time peak?
An all-time peak reference means that a correction happening during a bear market recovery will never exceed the original all-time high — so it would be invisible. Using a 252-day rolling peak gives each event its own local reference, allowing recoveries to contain their own sub-corrections.

### Why 45-day trough clustering?
A single market event often produces multiple contiguous blocks when prices temporarily bounce above the threshold then fall again. Clustering troughs within 45 calendar days merges these into one event without conflating genuinely separate events (which tend to be months apart).

### Why remove corrections nested inside bear markets?
A bear market by definition contains the same decline as any correction that starts at the same time. Keeping both would double-count the same price action under two different labels.

---

## Dependencies

- `numpy`
- `pandas`
- `matplotlib`
- `yfinance`
- `rich` *(optional — only required for `print_cycles_table()`)*

---

## License

MIT
