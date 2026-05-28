"""
Market Cycles Analysis Framework
=================================

Identify, classify, and visualise bear markets, corrections, and bull markets
from historical price data.

Public API
----------
Data
    download_price_data

Cycle detection
    identify_market_cycles
    summarize_recovery_cycles

Bull market identification
    identify_bull_markets
    summarize_bull_markets

Plotting
    plot_recovery_cycles
    plot_cycle_duration_bars
    plot_cycle_drawdown_bars

Reporting (requires: pip install rich)
    print_cycles_table
"""

from .data     import download_price_data
from .cycles   import identify_market_cycles, summarize_recovery_cycles
from .bulls    import identify_bull_markets, summarize_bull_markets
from .plotting import (
    plot_recovery_cycles,
    plot_cycle_duration_bars,
    plot_cycle_drawdown_bars,
)
from .reporting import print_cycles_table

__all__ = [
    "download_price_data",
    "identify_market_cycles",
    "summarize_recovery_cycles",
    "identify_bull_markets",
    "summarize_bull_markets",
    "plot_recovery_cycles",
    "plot_cycle_duration_bars",
    "plot_cycle_drawdown_bars",
    "print_cycles_table",
]
