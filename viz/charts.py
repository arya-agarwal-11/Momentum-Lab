import pandas as pd
import plotly.graph_objects as go


def plot_equity_curve(
    results,
    strategy_type="Long Only",
):
    """
    Plot the strategy equity curve against
    the NIFTY 50 benchmark.

    For a long-short strategy, also displays
    the long and short sides.
    """

    fig = go.Figure()

    # --------------------------------------------------------
    # Strategy
    # --------------------------------------------------------

    strategy_name = (
        "Long-Short Strategy"
        if strategy_type == "Long + Short"
        else "Momentum Strategy"
    )

    fig.add_trace(
        go.Scatter(
            x=results.index,
            y=results["Strategy"],
            mode="lines",
            name=strategy_name,
        )
    )

    # --------------------------------------------------------
    # Benchmark
    # --------------------------------------------------------

    fig.add_trace(
        go.Scatter(
            x=results.index,
            y=results["Benchmark"],
            mode="lines",
            name="NIFTY 50",
        )
    )

    # --------------------------------------------------------
    # Long / Short Components
    # --------------------------------------------------------

    if strategy_type == "Long + Short":

        if "Long Side" in results.columns:

            fig.add_trace(
                go.Scatter(
                    x=results.index,
                    y=results["Long Side"],
                    mode="lines",
                    name="Long Side",
                    line=dict(
                        dash="dot"
                    ),
                )
            )

        if "Short Side" in results.columns:

            fig.add_trace(
                go.Scatter(
                    x=results.index,
                    y=results["Short Side"],
                    mode="lines",
                    name="Short Side",
                    line=dict(
                        dash="dot"
                    ),
                )
            )

    fig.update_layout(
        height=500,
        xaxis_title="Date",
        yaxis_title="Growth of ₹1",
        hovermode="x unified",
    )

    return fig


def plot_drawdown(drawdown):
    """
    Plot portfolio drawdown over time.
    """

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=drawdown.index,
            y=drawdown,
            mode="lines",
            name="Drawdown",
            fill="tozeroy",
        )
    )

    fig.update_layout(
        height=350,
        xaxis_title="Date",
        yaxis_title="Drawdown",
        yaxis_tickformat=".0%",
        hovermode="x unified",
    )

    return fig


def plot_momentum_heatmap(
    heatmap_data,
    metric,
):
    """
    Create the momentum lookback /
    holding-period heatmap.
    """

    if metric in [
        "CAGR",
        "Volatility",
        "Max Drawdown",
    ]:

        text_values = (
            heatmap_data
            .map(
                lambda x:
                f"{x:.1%}"
                if pd.notna(x)
                else "N/A"
            )
        )

    else:

        text_values = (
            heatmap_data
            .map(
                lambda x:
                f"{x:.2f}"
                if pd.notna(x)
                else "N/A"
            )
        )

    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            text=text_values.values,
            texttemplate="%{text}",
            hovertemplate=(
                "Lookback: %{y}<br>"
                "Holding: %{x}<br>"
                f"{metric}: %{{z}}"
                "<extra></extra>"
            ),
            colorbar=dict(
                title=metric
            ),
        )
    )

    fig.update_layout(
        height=450,
        xaxis_title="Holding Period",
        yaxis_title="Momentum Lookback",
    )

    return fig

