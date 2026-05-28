"""
Price data download from Yahoo Finance.
"""

import pandas as pd
import yfinance as yf


def download_price_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    """
    Download adjusted closing prices from Yahoo Finance.

    Uses Adj Close (not Close) so that the price series is corrected for
    dividends and splits. Without adjustment, a dividend payment appears as
    a price drop and creates a spurious drawdown event.

    Parameters
    ----------
    ticker : Yahoo Finance ticker string (e.g. 'SPY', 'QQQ', '^GSPC')
    start  : start date string 'YYYY-MM-DD' (inclusive)
    end    : end date string 'YYYY-MM-DD' (exclusive in yfinance convention)

    Returns
    -------
    pd.DataFrame with DatetimeIndex and single column 'price'
    """
    df = yf.download(ticker, start=start, end=end,
                     auto_adjust=False, progress=False)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df[["Adj Close"]].dropna()
    df.rename(columns={"Adj Close": "price"}, inplace=True)
    df.index = pd.to_datetime(df.index)

    return df
