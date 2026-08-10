import numpy as np
import pandas as pd


def calculate_metrics(returns):
    """
    Calculate key performance and risk metrics.

    Returns:
        CAGR
        Sharpe Ratio
        Annualized Volatility
        Maximum Drawdown
    """

    returns = returns.dropna()

    if len(returns) < 2:

        return {
            "CAGR": np.nan,
            "Sharpe": np.nan,
            "Volatility": np.nan,
            "Max Drawdown": np.nan,
        }

    # --------------------------------------------------------
    # Equity Curve
    # --------------------------------------------------------

    equity_curve = (
        1 + returns
    ).cumprod()

    # --------------------------------------------------------
    # CAGR
    # --------------------------------------------------------

    years = len(returns) / 252

    if years <= 0:

        cagr = np.nan

    else:

        cagr = (
            equity_curve.iloc[-1]
            ** (1 / years)
            - 1
        )

    # --------------------------------------------------------
    # Annualized Volatility
    # --------------------------------------------------------

    volatility = (
        returns.std()
        * np.sqrt(252)
    )

    # --------------------------------------------------------
    # Sharpe Ratio
    # --------------------------------------------------------

    if returns.std() == 0:

        sharpe = np.nan

    else:

        sharpe = (
            returns.mean()
            / returns.std()
            * np.sqrt(252)
        )

    # --------------------------------------------------------
    # Maximum Drawdown
    # --------------------------------------------------------

    rolling_max = (
        equity_curve
        .cummax()
    )

    drawdown = (
        equity_curve
        / rolling_max
        - 1
    )

    max_drawdown = drawdown.min()

    return {
        "CAGR": cagr,
        "Sharpe": sharpe,
        "Volatility": volatility,
        "Max Drawdown": max_drawdown,
    }


def calculate_equity_curve(returns):
    """
    Convert a return series into a cumulative
    growth-of-$1 equity curve.
    """

    returns = returns.fillna(0)

    return (
        1 + returns
    ).cumprod()


def calculate_drawdown(returns):
    """
    Calculate the drawdown series from a return stream.
    """

    equity_curve = (
        calculate_equity_curve(
            returns
        )
    )

    rolling_max = (
        equity_curve
        .cummax()
    )

    drawdown = (
        equity_curve
        / rolling_max
        - 1
    )

    return drawdown

