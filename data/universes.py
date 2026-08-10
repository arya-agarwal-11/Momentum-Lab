
import io
import requests
import pandas as pd


# ============================================================
# OFFICIAL NSE CONSTITUENT FILES
# ============================================================

NSE_CSV_URLS = {
    "NIFTY 50": (
        "https://niftyindices.com/IndexConstituent/"
        "ind_nifty50list.csv"
    ),

    "NIFTY 100": (
        "https://niftyindices.com/IndexConstituent/"
        "ind_nifty100list.csv"
    ),

    "NIFTY 500": (
        "https://niftyindices.com/IndexConstituent/"
        "ind_nifty500list.csv"
    ),
}


# ============================================================
# LARGE-CAP TEST UNIVERSE
# ============================================================

LARGE_CAP_TEST_UNIVERSE = [
    "RELIANCE.NS",
    "TCS.NS",
    "HDFCBANK.NS",
    "INFY.NS",
    "ICICIBANK.NS",
    "HINDUNILVR.NS",
    "ITC.NS",
    "SBIN.NS",
    "BHARTIARTL.NS",
    "LT.NS",
    "AXISBANK.NS",
    "KOTAKBANK.NS",
    "MARUTI.NS",
    "SUNPHARMA.NS",
    "TATAMOTORS.NS",
    "WIPRO.NS",
    "HCLTECH.NS",
    "ASIANPAINT.NS",
    "BAJFINANCE.NS",
    "ADANIENT.NS",
]


# ============================================================
# DOWNLOAD CONSTITUENT CSV
# ============================================================

def get_nse_universe(index_name):
    """
    Download the current constituent list for an NSE index.

    Returns Yahoo Finance-compatible tickers such as:

        RELIANCE.NS
        TCS.NS
        INFY.NS
    """

    if index_name not in NSE_CSV_URLS:

        raise ValueError(
            f"Unsupported universe: {index_name}"
        )

    url = NSE_CSV_URLS[index_name]

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/151.0 Safari/537.36"
        ),
        "Accept": (
            "text/csv,"
            "application/csv,"
            "text/plain,"
            "*/*"
        ),
        "Referer": (
            "https://www.niftyindices.com/"
        ),
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=20,
        )

        response.raise_for_status()

    except requests.RequestException as error:

        raise RuntimeError(
            f"Unable to download the "
            f"{index_name} constituent file."
        ) from error

    # --------------------------------------------------------
    # Read CSV
    # --------------------------------------------------------

    try:

        df = pd.read_csv(
            io.BytesIO(
                response.content
            )
        )

    except Exception as error:

        raise RuntimeError(
            f"Unable to read the "
            f"{index_name} constituent file."
        ) from error

    # --------------------------------------------------------
    # Find SYMBOL column
    # --------------------------------------------------------

    symbol_column = None

    for column in df.columns:

        if column.strip().upper() in [
            "SYMBOL",
            "SYMBOLS",
        ]:

            symbol_column = column
            break

    if symbol_column is None:

        raise RuntimeError(
            f"Could not find a SYMBOL column "
            f"in the {index_name} file."
        )

    symbols = (
        df[symbol_column]
        .dropna()
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Convert to Yahoo Finance format
    # --------------------------------------------------------

    tickers = [
        f"{symbol}.NS"
        for symbol in symbols
        if symbol
    ]

    tickers = list(
        dict.fromkeys(tickers)
    )

    if not tickers:

        raise RuntimeError(
            f"No stocks found in the "
            f"{index_name} constituent file."
        )

    return tickers


# ============================================================
# GET UNIVERSE
# ============================================================

def get_universe(universe_name):
    """
    Return the ticker list for a selected universe.
    """

    if universe_name == (
        "Large-Cap Test Universe"
    ):

        return (
            LARGE_CAP_TEST_UNIVERSE.copy()
        )

    if universe_name in [
        "NIFTY 50",
        "NIFTY 100",
        "NIFTY 500",
    ]:

        return get_nse_universe(
            universe_name
        )

    raise ValueError(
        f"Unknown universe: "
        f"{universe_name}"
    )


# ============================================================
# AVAILABLE UNIVERSES
# ============================================================

def get_available_universes():
    """
    Return all universes available
    in the Streamlit interface.
    """

    return [
        "Large-Cap Test Universe",
        "NIFTY 50",
        "NIFTY 100",
        "NIFTY 500",
    ]