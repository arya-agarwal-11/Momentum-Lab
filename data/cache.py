from pathlib import Path

import pandas as pd


# ============================================================
# CACHE DIRECTORY
# ============================================================

CACHE_DIR = Path("data") / "cache"

CACHE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# CACHE PATH
# ============================================================

def get_cache_path(
    universe_name,
    years,
):
    """
    Generate a unique cache filename for a universe
    and requested backtest period.
    """

    safe_name = (
        universe_name
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
    )

    return (
        CACHE_DIR
        / f"{safe_name}_{years}y.parquet"
    )


# ============================================================
# LOAD CACHE
# ============================================================

def load_cached_data(
    universe_name,
    years,
):
    """
    Load previously downloaded price data.

    Returns None if no cache exists.
    """

    cache_path = get_cache_path(
        universe_name,
        years,
    )

    if not cache_path.exists():

        return None

    try:

        return pd.read_parquet(
            cache_path
        )

    except Exception:

        return None


# ============================================================
# SAVE CACHE
# ============================================================

def save_cached_data(
    data,
    universe_name,
    years,
):
    """
    Save downloaded price data to the local cache.
    """

    cache_path = get_cache_path(
        universe_name,
        years,
    )

    data.to_parquet(
        cache_path
    )


# ============================================================
# CLEAR CACHE
# ============================================================

def clear_cache():
    """
    Delete all locally cached market data.
    """

    if not CACHE_DIR.exists():

        return

    for file in CACHE_DIR.glob(
        "*.parquet"
    ):

        try:

            file.unlink()

        except OSError:

            pass

# idk testing testing