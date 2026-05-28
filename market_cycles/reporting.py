"""
Rich console table for market cycle analysis.

Requires: pip install rich
"""

import pandas as pd


def print_cycles_table(cycles: pd.DataFrame, top_n: int = None) -> None:
    """
    Print a formatted Rich table of market cycles with a statistics footer.

    Rows are color-coded by event type:
      Red   = Bear Market      (>= 20% drawdown)
      Blue  = Correction       (>= 10% drawdown)
      Teal  = Small Correction (<  10% drawdown)

    Rows are separated by type group with a section divider.
    Footer shows column averages. Three statistics panels below the table
    summarise each type separately.

    Parameters
    ----------
    cycles : output of identify_market_cycles()
    top_n  : number of worst drawdowns to show. None = show all.

    Requires: pip install rich
    """
    try:
        from rich.columns import Columns
        from rich.console import Console
        from rich         import box
        from rich.panel   import Panel
        from rich.table   import Table
        from rich.text    import Text
    except ImportError:
        raise ImportError(
            "The 'rich' package is required for print_cycles_table(). "
            "Install it with: pip install rich"
        )

    # ------------------------------------------------------------------
    # Prepare data
    # ------------------------------------------------------------------
    df = cycles.copy()

    if "market_type" not in df.columns:
        def _classify(dd: float) -> str:
            dd = abs(dd)
            if dd >= 0.20:   return "Bear Market"
            elif dd >= 0.10: return "Correction"
            else:            return "Small Correction"
        df["market_type"] = df["drawdown_pct"].apply(_classify)

    type_col = "market_type"

    df = df.sort_values("drawdown_pct").reset_index(drop=True)
    if top_n is not None:
        df = df.head(top_n)

    # ------------------------------------------------------------------
    # Color scheme
    # ------------------------------------------------------------------
    TYPE_COLORS = {
        "Bear Market":      "bold #CC2200",
        "Correction":       "bold blue",
        "Small Correction": "#0E8080",
    }

    # ------------------------------------------------------------------
    # Footer statistics
    # ------------------------------------------------------------------
    avg_dtt  = df["days_to_trough"].mean()
    avg_rec  = df["days_to_recovery"].mean()
    avg_cyc  = df["full_cycle_days"].mean()
    FOOTER   = "bold #8E44AD"

    # ------------------------------------------------------------------
    # Build table
    # ------------------------------------------------------------------
    console = Console(width=140)

    table = Table(
        title="[bold white]Market Cycle Analysis[/bold white]",
        box=box.SIMPLE_HEAD,
        show_header=True,
        header_style="bold white on #0A2A4A",
        title_style="bold white on #0A2A4A",
        border_style="#404040",
        show_footer=True,
        padding=(0, 2),
        min_width=130,
    )

    table.add_column("Type",       justify="left",   width=18,
                     footer=f"[{FOOTER}]Statistics[/{FOOTER}]")
    table.add_column("Peak",       justify="center", width=12, footer="")
    table.add_column("Trough",     justify="center", width=12, footer="")
    table.add_column("Recovery",   justify="center", width=12, footer="")
    table.add_column("DD %",       justify="right",  width=8,  footer="")
    table.add_column("Days↓",      justify="right",  width=8,
                     footer=f"[{FOOTER}]avg {avg_dtt:.0f}[/{FOOTER}]")
    table.add_column("Days Rec",   justify="right",  width=10,
                     footer=f"[{FOOTER}]avg {avg_rec:.0f}[/{FOOTER}]")
    table.add_column("Full Cycle", justify="right",  width=12,
                     footer=f"[{FOOTER}]avg {avg_cyc:.0f}[/{FOOTER}]")

    prev_type = None

    for _, row in df.iterrows():
        ctype = row[type_col]
        color = TYPE_COLORS.get(ctype, "white")

        peak_str     = str(row["peak_date"])[:10]
        trough_str   = str(row["trough_date"])[:10]
        recovery_str = str(row["recovery_date"])[:10] \
                       if pd.notna(row["recovery_date"]) else "—"
        dd_str  = f"{row['drawdown_pct']*100:.1f}%"
        dtt_str = f"{int(row['days_to_trough'])}"
        rec_str = f"{int(row['days_to_recovery'])}" \
                  if pd.notna(row["days_to_recovery"]) else "—"
        cyc_str = f"{int(row['full_cycle_days'])}"

        if prev_type is not None and ctype != prev_type:
            table.add_section()

        table.add_row(
            f"[{color}]{ctype}[/{color}]",
            f"[white]{peak_str}[/white]",
            f"[white]{trough_str}[/white]",
            f"[white]{recovery_str}[/white]",
            f"[{color}]{dd_str}[/{color}]",
            f"[white]{dtt_str}[/white]",
            f"[white]{rec_str}[/white]",
            f"[white]{cyc_str}[/white]",
        )
        prev_type = ctype

    console.print()
    console.print(table)

    # ------------------------------------------------------------------
    # Statistics panels — one per event type
    # ------------------------------------------------------------------
    bears = df[df[type_col] == "Bear Market"]
    corr  = df[df[type_col] == "Correction"]
    small = df[df[type_col] == "Small Correction"]

    def _stat_panel(label: str, subset: pd.DataFrame,
                    color: str, border: str) -> Panel:
        if len(subset) == 0:
            return Panel(
                Text("  No events", style="dim"),
                title=f"[bold {color}]{label}[/bold {color}]",
                border_style=border, padding=(0, 2),
            )

        rec_sub = subset[subset["recovered"]]
        t = Text()
        t.append(f"  Count          : {len(subset)}\n",  style="white")
        t.append(f"  Avg DD         : {subset['drawdown_pct'].mean()*100:.1f}%\n",
                 style=color)
        t.append(f"  Worst DD       : {subset['drawdown_pct'].min()*100:.1f}%\n",
                 style=f"bold {color}")
        t.append(f"  Avg Days↓      : {subset['days_to_trough'].mean():.0f}d\n",
                 style="white")
        if len(rec_sub) > 0:
            t.append(f"  Avg Days Rec   : {rec_sub['days_to_recovery'].mean():.0f}d\n",
                     style="white")
            t.append(f"  Avg Full Cycle : {rec_sub['full_cycle_days'].mean():.0f}d\n",
                     style="white")

        return Panel(
            t,
            title=f"[bold {color}]{label}[/bold {color}]",
            border_style=border,
            padding=(0, 2),
        )

    console.print(Columns([
        _stat_panel("Bear Markets",      bears, "#CC2200", "#CC2200"),
        _stat_panel("Corrections",       corr,  "blue",    "blue"),
        _stat_panel("Small Corrections", small, "#0E8080", "#0E8080"),
    ], equal=True))

    console.print()
