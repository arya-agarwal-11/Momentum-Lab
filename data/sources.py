import pandas as pd
import yfinance as yf

from data.cache import (
    load_cached_data,
    save_cached_data,
)


# ============================================================
# DOWNLOAD RAW PRICE DATA
# ============================================================

def download_data(
    tickers,
    years,
):
    """
    Download historical adjusted closing prices
    for a list of tickers.

    Extra historical data is downloaded before the
    requested period so momentum calculations have
    enough lookback history.
    """

    end_date = pd.Timestamp.today()

    start_date = (
        end_date
        - pd.DateOffset(years=years)
        - pd.DateOffset(days=400)
    )

    data = yf.download(
        list(tickers),
        start=start_date,
        end=end_date,
        auto_adjust=True,
        progress=False,
    )

    if data.empty:

        return None

    # --------------------------------------------------------
    # Handle multi-level Yahoo Finance columns
    # --------------------------------------------------------

    if isinstance(
        data.columns,
        pd.MultiIndex,
    ):

        if "Close" in data.columns.levels[0]:

            prices = data["Close"]

        else:

            prices = data.xs(
                "Close",
                axis=1,
                level=0,
            )

    else:

        prices = data[["Close"]]

    # --------------------------------------------------------
    # Remove stocks with no data
    # --------------------------------------------------------

    prices = prices.dropna(
        axis=1,
        how="all",
    )

    # --------------------------------------------------------
    # Sort chronologically
    # --------------------------------------------------------

    prices = prices.sort_index()

    return prices


# ============================================================
# LOAD OR DOWNLOAD DATA
# ============================================================

def load_or_download_data(
    tickers,
    universe_name,
    years,
):
    """
    Load cached data if available.

    Otherwise download the data and cache it.

    This keeps app.py independent from the
    underlying data source.
    """

    # --------------------------------------------------------
    # Check cache
    # --------------------------------------------------------

    cached_data = load_cached_data(
        universe_name,
        years,
    )

    if cached_data is not None:

        return cached_data

    # --------------------------------------------------------
    # Download
    # --------------------------------------------------------

    prices = download_data(
        tickers,
        years,
    )

    if prices is None:

        return None

    # --------------------------------------------------------
    # Save cache
    # --------------------------------------------------------

    save_cached_data(
        prices,
        universe_name,
        years,
    )

    return prices


# ============================================================
# DOWNLOAD BENCHMARK
# ============================================================

def download_benchmark(
    years,
):
    """
    Download historical NIFTY 50 prices.
    """

    end_date = pd.Timestamp.today()

    start_date = (
        end_date
        - pd.DateOffset(years=years)
        - pd.DateOffset(days=400)
    )

    data = yf.download(
        "^NSEI",
        start=start_date,
        end=end_date,
        auto_adjust=True,
        progress=False,
    )

    if data.empty:

        return None

    # --------------------------------------------------------
    # Handle Yahoo's MultiIndex format
    # --------------------------------------------------------

    if isinstance(
        data.columns,
        pd.MultiIndex,
    ):

        prices = data[
            "Close"
        ].squeeze()

    else:

        prices = data[
            "Close"
        ]

    return prices.sort_index()

