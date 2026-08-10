import streamlit as st
import pandas as pd
import numpy as np

from data.sources import (
    load_or_download_data,
    download_benchmark,
)

from data.universes import (
    get_universe,
    get_available_universes,
)

from core.momentum import (
    run_momentum_backtest,
)

from core.metrics import (
    calculate_metrics,
    calculate_equity_curve,
    calculate_drawdown,
)

from viz.charts import (
    plot_equity_curve,
    plot_drawdown,
    plot_momentum_heatmap,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Momentum Lab",
    page_icon="📈",
    layout="wide",
)


# ============================================================
# CONSTANTS
# ============================================================

LOOKBACKS = {
    "1 Month": 21,
    "3 Months": 63,
    "6 Months": 126,
    "12 Months": 252,
}

HOLDING_PERIODS = {
    "1 Week": 5,
    "1 Month": 21,
    "3 Months": 63,
    "6 Months": 126,
}

PORTFOLIO_SIZES = {
    "Top 10%": 0.10,
    "Top 20%": 0.20,
    "Top 30%": 0.30,
    "Top 50%": 0.50,
}


# ============================================================
# STRATEGY RUNNER
# ============================================================

def run_single_strategy(
    prices,
    lookback_name,
    holding_name,
    long_portfolio_name,
    strategy_type,
    short_portfolio_name=None,
):

    lookback_days = LOOKBACKS[
        lookback_name
    ]

    holding_days = HOLDING_PERIODS[
        holding_name
    ]

    long_percent = PORTFOLIO_SIZES[
        long_portfolio_name
    ]

    if (
        strategy_type == "Long + Short"
        and short_portfolio_name is not None
    ):

        short_percent = PORTFOLIO_SIZES[
            short_portfolio_name
        ]

    else:

        short_percent = 0.0

    return run_momentum_backtest(
        prices=prices,
        lookback_days=lookback_days,
        holding_days=holding_days,
        long_percent=long_percent,
        short_percent=short_percent,
        strategy_type=strategy_type,
    )


# ============================================================
# MOMENTUM EXPLORER
# ============================================================

def run_momentum_explorer(
    prices,
    selected_lookbacks,
    selected_holdings,
    long_portfolio_name,
    strategy_type="Long Only",
    short_portfolio_name=None,
):

    results = []

    for lookback_name in selected_lookbacks:

        for holding_name in selected_holdings:

            (
                portfolio_returns,
                long_returns,
                short_returns,
                holdings,
            ) = run_single_strategy(
                prices,
                lookback_name,
                holding_name,
                long_portfolio_name,
                strategy_type,
                short_portfolio_name,
            )

            metrics = calculate_metrics(
                portfolio_returns
            )

            results.append(
                {
                    "Lookback": lookback_name,
                    "Holding Period": holding_name,
                    "CAGR": metrics["CAGR"],
                    "Sharpe": metrics["Sharpe"],
                    "Volatility": metrics[
                        "Volatility"
                    ],
                    "Max Drawdown": metrics[
                        "Max Drawdown"
                    ],
                }
            )

    return pd.DataFrame(results)


# ============================================================
# POSITION RETURN
# ============================================================

def calculate_position_return(
    prices,
    ticker,
    entry_date,
    position_type,
):
    """
    Calculate the return of a stock since it entered
    the current portfolio.

    Long:
        (Current - Entry) / Entry

    Short:
        (Entry - Current) / Entry
    """

    if ticker not in prices.columns:

        return np.nan

    ticker_prices = (
        prices[ticker]
        .dropna()
    )

    if ticker_prices.empty:

        return np.nan

    # --------------------------------------------------------
    # Entry price
    # --------------------------------------------------------

    entry_prices = ticker_prices[
        ticker_prices.index <= entry_date
    ]

    if entry_prices.empty:

        return np.nan

    entry_price = (
        entry_prices.iloc[-1]
    )

    # --------------------------------------------------------
    # Current price
    # --------------------------------------------------------

    current_price = (
        ticker_prices.iloc[-1]
    )

    if (
        pd.isna(entry_price)
        or pd.isna(current_price)
        or entry_price == 0
    ):

        return np.nan

    # --------------------------------------------------------
    # Long / Short return
    # --------------------------------------------------------

    if position_type == "LONG":

        return (
            current_price - entry_price
        ) / entry_price

    elif position_type == "SHORT":

        return (
            entry_price - current_price
        ) / entry_price

    return np.nan


# ============================================================
# FORMAT PORTFOLIO RETURN
# ============================================================

def format_return(value):

    if pd.isna(value):

        return "N/A"

    return f"{value:+.2%}"


# ============================================================
# STYLE PORTFOLIO RETURNS
# ============================================================

def style_returns(
    dataframe,
    return_column="Return",
):
    """
    Color positive returns green and negative returns red.
    """

    def color_return(value):

        if not isinstance(
            value,
            str,
        ):

            return ""

        if value.startswith("+"):

            return "color: green; font-weight: bold;"

        if value.startswith("-"):

            return "color: red; font-weight: bold;"

        return ""

    return (
        dataframe.style
        .map(
            color_return,
            subset=[return_column],
        )
    )


# ============================================================
# HEADER
# ============================================================

st.title("📈 Momentum Lab")

st.markdown(
    """
    **An interactive research platform for exploring
    price momentum in equities.**
    """
)

st.divider()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header(
    "Strategy Parameters"
)

universe_name = st.sidebar.selectbox(
    "Universe",
    get_available_universes(),
)

strategy_type = st.sidebar.radio(
    "Strategy Type",
    [
        "Long Only",
        "Long + Short",
    ],
)

momentum_lookback = st.sidebar.selectbox(
    "Momentum Lookback",
    list(LOOKBACKS.keys()),
    index=1,
)

holding_period = st.sidebar.selectbox(
    "Holding Period",
    list(HOLDING_PERIODS.keys()),
    index=1,
)

long_portfolio_size = st.sidebar.selectbox(
    "Long Selection",
    list(PORTFOLIO_SIZES.keys()),
    index=1,
)

if strategy_type == "Long + Short":

    short_portfolio_size = st.sidebar.selectbox(
        "Short Selection",
        list(PORTFOLIO_SIZES.keys()),
        index=1,
    )

else:

    short_portfolio_size = None

years = st.sidebar.slider(
    "Backtest Period",
    min_value=1,
    max_value=10,
    value=5,
)

run_analysis = st.sidebar.button(
    "🚀 Run Analysis",
    type="primary",
)


# ============================================================
# RUN ANALYSIS
# ============================================================

if run_analysis:

    # --------------------------------------------------------
    # Universe
    # --------------------------------------------------------

    with st.spinner(
        f"Loading {universe_name} constituents..."
    ):

        try:

            tickers = get_universe(
                universe_name
            )

        except Exception as error:

            st.error(
                f"Unable to load {universe_name}: "
                f"{error}"
            )

            st.stop()

    # --------------------------------------------------------
    # Market Data
    # --------------------------------------------------------

    with st.spinner(
        "Loading market data..."
    ):

        prices = load_or_download_data(
            tickers=tuple(tickers),
            universe_name=universe_name,
            years=years,
        )

    if prices is None or prices.empty:

        st.error(
            "Unable to download market data."
        )

        st.stop()

    # --------------------------------------------------------
    # Momentum Backtest
    # --------------------------------------------------------

    with st.spinner(
        "Running momentum backtest..."
    ):

        (
            strategy_returns,
            long_returns,
            short_returns,
            holdings,
        ) = run_single_strategy(
            prices,
            momentum_lookback,
            holding_period,
            long_portfolio_size,
            strategy_type,
            short_portfolio_size,
        )

    # --------------------------------------------------------
    # Benchmark
    # --------------------------------------------------------

    benchmark_prices = (
        download_benchmark(years)
    )

    if benchmark_prices is not None:

        benchmark_prices = (
            benchmark_prices
            .reindex(
                strategy_returns.index
            )
            .ffill()
        )

        benchmark_returns = (
            benchmark_prices
            .pct_change()
            .fillna(0)
        )

    else:

        benchmark_returns = pd.Series(
            0.0,
            index=strategy_returns.index,
        )

    # --------------------------------------------------------
    # Equity Curves
    # --------------------------------------------------------

    strategy_curve = (
        calculate_equity_curve(
            strategy_returns
        )
    )

    benchmark_curve = (
        calculate_equity_curve(
            benchmark_returns
        )
    )

    results = pd.DataFrame(
        {
            "Strategy": strategy_curve,
            "Benchmark": benchmark_curve,
        }
    )

    # --------------------------------------------------------
    # Long / Short Curves
    # --------------------------------------------------------

    if strategy_type == "Long + Short":

        long_curve = (
            calculate_equity_curve(
                0.5 * long_returns
            )
        )

        short_curve = (
            calculate_equity_curve(
                short_returns
            )
        )

        results["Long Side"] = (
            long_curve
        )

        results["Short Side"] = (
            short_curve
        )

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    metrics = calculate_metrics(
        strategy_returns
    )

    # --------------------------------------------------------
    # Store Results
    # --------------------------------------------------------

    st.session_state["prices"] = prices
    st.session_state["results"] = results
    st.session_state["metrics"] = metrics
    st.session_state["holdings"] = holdings
    st.session_state["strategy_type"] = strategy_type
    st.session_state["long_returns"] = long_returns
    st.session_state["short_returns"] = short_returns

    # Store selected parameters so that the displayed
    # strategy always matches the strategy that was run.

    st.session_state[
        "momentum_lookback"
    ] = momentum_lookback

    st.session_state[
        "holding_period"
    ] = holding_period

    st.session_state[
        "long_portfolio_size"
    ] = long_portfolio_size

    st.session_state[
        "short_portfolio_size"
    ] = short_portfolio_size

    st.session_state[
        "universe_name"
    ] = universe_name


# ============================================================
# LANDING PAGE
# ============================================================

if "results" not in st.session_state:

    st.info(
        "👈 Choose your parameters and click "
        "**Run Analysis** to start."
    )

    st.subheader(
        "Momentum Lab"
    )

    st.markdown(
        """
        Momentum Lab lets you investigate whether stocks
        that have performed strongly in the past continue
        to perform strongly in the future.

        The platform supports both **long-only** momentum
        and **long-short** momentum strategies.
        """
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(
            """
            ### 📊 Rank

            Rank stocks according to their
            historical price momentum.
            """
        )

    with col2:

        st.markdown(
            """
            ### 💼 Portfolio

            Go long the strongest stocks and,
            optionally, short the weakest.
            """
        )

    with col3:

        st.markdown(
            """
            ### 🔬 Experiment

            Explore how momentum changes when
            you change the strategy parameters.
            """
        )

    st.stop()


# ============================================================
# RETRIEVE RESULTS
# ============================================================

results = st.session_state[
    "results"
]

metrics = st.session_state[
    "metrics"
]

holdings = st.session_state[
    "holdings"
]

strategy_type = st.session_state[
    "strategy_type"
]

long_returns = st.session_state[
    "long_returns"
]

short_returns = st.session_state[
    "short_returns"
]

prices = st.session_state[
    "prices"
]

# Use the parameters that actually produced the results.

momentum_lookback = st.session_state[
    "momentum_lookback"
]

holding_period = st.session_state[
    "holding_period"
]

long_portfolio_size = st.session_state[
    "long_portfolio_size"
]

short_portfolio_size = st.session_state[
    "short_portfolio_size"
]

universe_name = st.session_state[
    "universe_name"
]


# ============================================================
# CURRENT STRATEGY
# ============================================================

st.subheader(
    "Current Strategy"
)

cols = st.columns(6)

current_parameters = [
    (
        "Universe",
        universe_name,
    ),
    (
        "Strategy",
        strategy_type,
    ),
    (
        "Momentum",
        momentum_lookback,
    ),
    (
        "Holding Period",
        holding_period,
    ),
    (
        "Long Selection",
        long_portfolio_size,
    ),
    (
        "Short Selection",
        short_portfolio_size
        if strategy_type == "Long + Short"
        else "None",
    ),
]

for col, (label, value) in zip(
    cols,
    current_parameters,
):

    with col:

        st.caption(label)

        st.write(
            f"**{value}**"
        )


# ============================================================
# EXPOSURE
# ============================================================

if strategy_type == "Long + Short":

    st.divider()

    st.subheader(
        "Portfolio Exposure"
    )

    exposure_cols = st.columns(4)

    exposure_cols[0].metric(
        "Long Exposure",
        "50%",
    )

    exposure_cols[1].metric(
        "Short Exposure",
        "-50%",
    )

    exposure_cols[2].metric(
        "Net Exposure",
        "0%",
    )

    exposure_cols[3].metric(
        "Gross Exposure",
        "100%",
    )


# ============================================================
# PERFORMANCE
# ============================================================

st.divider()

st.subheader(
    "Performance"
)

metric_cols = st.columns(4)

metric_cols[0].metric(
    "CAGR",
    f"{metrics['CAGR']:.2%}",
)

metric_cols[1].metric(
    "Sharpe",
    f"{metrics['Sharpe']:.2f}",
)

metric_cols[2].metric(
    "Volatility",
    f"{metrics['Volatility']:.2%}",
)

metric_cols[3].metric(
    "Max Drawdown",
    f"{metrics['Max Drawdown']:.2%}",
)


# ============================================================
# EQUITY CURVE
# ============================================================

st.subheader(
    "Cumulative Returns"
)

equity_fig = plot_equity_curve(
    results,
    strategy_type,
)

st.plotly_chart(
    equity_fig,
    use_container_width=True,
)


# ============================================================
# MOMENTUM EXPLORER
# ============================================================

st.divider()

st.header(
    "🔬 Momentum Explorer"
)

st.markdown(
    """
    Explore how strategy performance changes across
    different momentum lookbacks and holding periods.
    """
)

explorer_col1, explorer_col2 = st.columns(2)

with explorer_col1:

    selected_lookbacks = st.multiselect(
        "Momentum Lookbacks",
        list(LOOKBACKS.keys()),
        default=[
            "1 Month",
            "3 Months",
            "6 Months",
            "12 Months",
        ],
    )

with explorer_col2:

    selected_holdings = st.multiselect(
        "Holding Periods",
        list(HOLDING_PERIODS.keys()),
        default=[
            "1 Week",
            "1 Month",
            "3 Months",
        ],
    )

explorer_metric = st.selectbox(
    "Metric to Explore",
    [
        "Sharpe",
        "CAGR",
        "Volatility",
        "Max Drawdown",
    ],
)

run_explorer = st.button(
    "🔬 Run Momentum Experiment",
)


if run_explorer:

    if (
        len(selected_lookbacks) == 0
        or len(selected_holdings) == 0
    ):

        st.warning(
            "Select at least one lookback and "
            "one holding period."
        )

    else:

        with st.spinner(
            "Running momentum experiments..."
        ):

            explorer_results = (
                run_momentum_explorer(
                    prices=st.session_state[
                        "prices"
                    ],
                    selected_lookbacks=(
                        selected_lookbacks
                    ),
                    selected_holdings=(
                        selected_holdings
                    ),
                    long_portfolio_name=(
                        long_portfolio_size
                    ),
                    strategy_type=(
                        strategy_type
                    ),
                    short_portfolio_name=(
                        short_portfolio_size
                    ),
                )
            )

        heatmap_data = (
            explorer_results
            .pivot(
                index="Lookback",
                columns="Holding Period",
                values=explorer_metric,
            )
        )

        lookback_order = [
            x
            for x in LOOKBACKS
            if x in heatmap_data.index
        ]

        holding_order = [
            x
            for x in HOLDING_PERIODS
            if x in heatmap_data.columns
        ]

        heatmap_data = (
            heatmap_data
            .reindex(
                index=lookback_order,
                columns=holding_order,
            )
        )

        st.subheader(
            f"{explorer_metric} by Momentum Horizon"
        )

        heatmap_fig = (
            plot_momentum_heatmap(
                heatmap_data,
                explorer_metric,
            )
        )

        st.plotly_chart(
            heatmap_fig,
            use_container_width=True,
        )

        st.subheader(
            "Experiment Results"
        )

        display_results = (
            explorer_results.copy()
        )

        display_results["CAGR"] = (
            display_results["CAGR"].map(
                lambda x:
                f"{x:.2%}"
                if pd.notna(x)
                else "N/A"
            )
        )

        display_results["Sharpe"] = (
            display_results["Sharpe"].map(
                lambda x:
                f"{x:.2f}"
                if pd.notna(x)
                else "N/A"
            )
        )

        display_results["Volatility"] = (
            display_results["Volatility"].map(
                lambda x:
                f"{x:.2%}"
                if pd.notna(x)
                else "N/A"
            )
        )

        display_results["Max Drawdown"] = (
            display_results[
                "Max Drawdown"
            ].map(
                lambda x:
                f"{x:.2%}"
                if pd.notna(x)
                else "N/A"
            )
        )

        st.dataframe(
            display_results,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# DRAWDOWN
# ============================================================

st.divider()

st.subheader(
    "Drawdown"
)

drawdown = calculate_drawdown(
    strategy_returns
)

drawdown_fig = plot_drawdown(
    drawdown
)

st.plotly_chart(
    drawdown_fig,
    use_container_width=True,
)


# ============================================================
# LATEST HOLDINGS
# ============================================================

st.divider()

st.subheader(
    "Latest Portfolio"
)

if holdings:

    latest_date = max(
        holdings.keys()
    )

    latest_holdings = holdings[
        latest_date
    ]

    # --------------------------------------------------------
    # LONG POSITIONS
    # --------------------------------------------------------

    long_tickers = latest_holdings.get(
        "long",
        [],
    )

    long_momentum = latest_holdings.get(
        "long_momentum",
        {},
    )

    long_data = []

    for ticker in long_tickers:

        position_return = (
            calculate_position_return(
                prices=prices,
                ticker=ticker,
                entry_date=latest_date,
                position_type="LONG",
            )
        )

        momentum_score = (
            long_momentum.get(
                ticker,
                np.nan,
            )
        )

        long_data.append(
            {
                "Ticker": ticker,
                "Momentum": format_return(
                    momentum_score
                ),
                "Return": format_return(
                    position_return
                ),
            }
        )

    long_df = pd.DataFrame(
        long_data
    )

    # --------------------------------------------------------
    # SHORT POSITIONS
    # --------------------------------------------------------

    short_tickers = latest_holdings.get(
        "short",
        [],
    )

    short_momentum = latest_holdings.get(
        "short_momentum",
        {},
    )

    short_data = []

    for ticker in short_tickers:

        position_return = (
            calculate_position_return(
                prices=prices,
                ticker=ticker,
                entry_date=latest_date,
                position_type="SHORT",
            )
        )

        momentum_score = (
            short_momentum.get(
                ticker,
                np.nan,
            )
        )

        short_data.append(
            {
                "Ticker": ticker,
                "Momentum": format_return(
                    momentum_score
                ),
                "Return": format_return(
                    position_return
                ),
            }
        )

    short_df = pd.DataFrame(
        short_data
    )

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    if strategy_type == "Long + Short":

        holding_col1, holding_col2 = (
            st.columns(2)
        )

        with holding_col1:

            st.markdown(
                "### 🟢 Long"
            )

            if not long_df.empty:

                st.dataframe(
                    style_returns(
                        long_df
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No long positions."
                )

        with holding_col2:

            st.markdown(
                "### 🔴 Short"
            )

            if not short_df.empty:

                st.dataframe(
                    style_returns(
                        short_df
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No short positions."
                )

    else:

        if not long_df.empty:

            st.dataframe(
                style_returns(
                    long_df
                ),
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "No positions."
            )

    st.caption(
        f"Portfolio selected on "
        f"{latest_date.strftime('%d %b %Y')}"
    )

    st.caption(
        "Momentum is the price return over the selected "
        "lookback period at the time of portfolio selection. "
        "Return is the position's performance since selection."
    )


