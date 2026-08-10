import numpy as np
import pandas as pd


def run_momentum_backtest(
    prices,
    lookback_days,
    holding_days,
    long_percent,
    short_percent=0.0,
    strategy_type="Long Only",
):
    """
    Run a cross-sectional momentum strategy.

    Long Only:
        Buy the top X% of stocks ranked by momentum.

    Long + Short:
        Long the top X% and short the bottom X%.

    Momentum is calculated as:

        Price today / Price lookback_days ago - 1

    The momentum score used to select each stock is stored
    alongside the portfolio holdings so that the UI can show
    the actual signal that caused the stock to be selected.
    """

    prices = prices.dropna(
        axis=1,
        how="all",
    )

    returns = prices.pct_change()

    # ========================================================
    # CALCULATE MOMENTUM
    # ========================================================

    momentum = (
        prices
        / prices.shift(lookback_days)
        - 1
    )

    # ========================================================
    # INITIALIZE OUTPUT SERIES
    # ========================================================

    portfolio_returns = pd.Series(
        0.0,
        index=prices.index,
    )

    long_returns = pd.Series(
        0.0,
        index=prices.index,
    )

    short_returns = pd.Series(
        0.0,
        index=prices.index,
    )

    holdings_history = {}

    # Rebalance every holding_period
    rebalance_dates = prices.index[
        lookback_days::holding_days
    ]

    # ========================================================
    # BACKTEST
    # ========================================================

    for i, rebalance_date in enumerate(
        rebalance_dates
    ):

        scores = momentum.loc[
            rebalance_date
        ].dropna()

        if len(scores) < 2:
            continue

        # ====================================================
        # LONG PORTFOLIO
        # ====================================================

        n_long = max(
            1,
            int(
                np.ceil(
                    len(scores)
                    * long_percent
                )
            ),
        )

        long_stocks = (
            scores
            .sort_values(
                ascending=False
            )
            .head(n_long)
            .index
        )

        # ====================================================
        # SHORT PORTFOLIO
        # ====================================================

        short_stocks = []

        if (
            strategy_type == "Long + Short"
            and short_percent > 0
        ):

            n_short = max(
                1,
                int(
                    np.ceil(
                        len(scores)
                        * short_percent
                    )
                ),
            )

            short_stocks = (
                scores
                .sort_values(
                    ascending=True
                )
                .head(n_short)
                .index
            )

        # ====================================================
        # SAVE HOLDINGS + MOMENTUM SCORES
        # ====================================================

        holdings_history[
            rebalance_date
        ] = {
            "long": list(long_stocks),
            "short": list(short_stocks),

            # Store the actual momentum score
            # at the time of selection.
            "long_momentum": {
                ticker: scores[ticker]
                for ticker in long_stocks
            },

            "short_momentum": {
                ticker: scores[ticker]
                for ticker in short_stocks
            },
        }

        # ====================================================
        # DETERMINE HOLDING PERIOD
        # ====================================================

        if i + 1 < len(rebalance_dates):

            next_rebalance = (
                rebalance_dates[i + 1]
            )

        else:

            next_rebalance = prices.index[-1]

        holding_dates = prices.index[
            (
                prices.index
                > rebalance_date
            )
            & (
                prices.index
                <= next_rebalance
            )
        ]

        if len(holding_dates) == 0:
            continue

        # ====================================================
        # LONG RETURNS
        # ====================================================

        selected_long_returns = (
            returns.loc[
                holding_dates,
                long_stocks,
            ]
        )

        daily_long_return = (
            selected_long_returns
            .mean(axis=1)
            .fillna(0)
        )

        # ====================================================
        # SHORT RETURNS
        # ====================================================

        if len(short_stocks) > 0:

            selected_short_returns = (
                returns.loc[
                    holding_dates,
                    short_stocks,
                ]
            )

            daily_short_return = (
                selected_short_returns
                .mean(axis=1)
                .fillna(0)
            )

        else:

            daily_short_return = pd.Series(
                0.0,
                index=holding_dates,
            )

        # ====================================================
        # COMBINE LONG + SHORT
        # ====================================================

        if strategy_type == "Long Only":

            daily_portfolio_return = (
                daily_long_return
            )

        else:

            # 50% allocated to longs
            # 50% allocated to shorts
            #
            # A short position profits when the
            # underlying stock falls.

            daily_portfolio_return = (
                0.5 * daily_long_return
                - 0.5 * daily_short_return
            )

        # ====================================================
        # STORE RETURNS
        # ====================================================

        long_returns.loc[
            holding_dates
        ] = daily_long_return

        short_returns.loc[
            holding_dates
        ] = -daily_short_return

        portfolio_returns.loc[
            holding_dates
        ] = daily_portfolio_return

    return (
        portfolio_returns,
        long_returns,
        short_returns,
        holdings_history,
    )

