"""Q5: Monthly Housing–SIRTA patterns and lag correlations."""
import numpy as np
import pandas as pd
import plotly.express as px


def _prepare(df):
    d = df.copy()
    if d.empty:
        raise ValueError("No monthly data for these filters.")

    d["date"] = pd.to_datetime(
        d["year_month"].astype(str).str[:7] + "-01",
        errors="coerce"
    )

    for col in ("h_filings_total", "t_crashes"):
        d[col] = pd.to_numeric(d[col], errors="coerce").fillna(0)

    return d.dropna(subset=["date"]).sort_values(["borough", "date"])


def make_fig(df):
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go

    d = _prepare(df)

    for source, output in (
        ("h_filings_total", "housing_index"),
        ("t_crashes", "sirta_index")
    ):
        d[output] = d.groupby("borough")[source].transform(
            lambda x: 100 * x / x.mean()
            if x.mean() > 0 else np.nan
        )

    boroughs = [
        b for b in
        ["Bronx", "Brooklyn", "Manhattan", "Queens", "Staten Island"]
        if b in d["borough"].unique()
    ]

    if not boroughs:
        raise ValueError("No borough data available.")

    fig = make_subplots(
        rows=len(boroughs),
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.065
    )

    for i, borough in enumerate(boroughs, start=1):
        group = d[d["borough"] == borough].sort_values("date")

        fig.add_trace(
            go.Scatter(
                x=group["date"],
                y=group["housing_index"],
                mode="lines",
                name="Housing filings",
                line=dict(color="#5271FF", width=2.5),
                legendgroup="Housing",
                showlegend=(i == 1),
                hovertemplate="%{x|%b %Y}<br>Housing index: %{y:.1f}<extra></extra>"
            ),
            row=i, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=group["date"],
                y=group["sirta_index"],
                mode="lines",
                name="SIRTA serious crashes",
                line=dict(color="#FF684B", width=2.5),
                legendgroup="SIRTA",
                showlegend=(i == 1),
                hovertemplate="%{x|%b %Y}<br>SIRTA index: %{y:.1f}<extra></extra>"
            ),
            row=i, col=1
        )

        # Borough name inside the panel, not in the outer margin.
        fig.add_annotation(
            x=0.012,
            y=fig.get_subplot(i, 1).yaxis.domain[1] - 0.008,
            xref="paper",
            yref="paper",
            text=f"<b>{borough}</b>",
            showarrow=False,
            xanchor="left",
            yanchor="top",
            font=dict(size=13, color="#243C60"),
            bgcolor="rgba(255,255,255,0.88)",
            borderpad=4
        )

        fig.update_yaxes(
            title_text="",
            showgrid=True,
            gridcolor="#E7ECF3",
            zeroline=False,
            row=i,
            col=1
        )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="#E7ECF3",
        zeroline=False,
        tickformat="%b %Y",
        dtick="M6"
    )

    fig.update_xaxes(
        title_text="Month",
        row=len(boroughs),
        col=1
    )

    fig.update_layout(
        title=dict(
            text="Q5: Monthly Housing and SIRTA Patterns by Borough",
            x=0.02,
            font=dict(size=20)
        ),
        height=920,
        autosize=True,
        margin=dict(l=55, r=25, t=115, b=60),
        paper_bgcolor="white",
        plot_bgcolor="white",
        hovermode="x",
        legend=dict(
            orientation="h",
            x=0,
            y=1.065,
            xanchor="left",
            yanchor="bottom",
            bgcolor="rgba(255,255,255,0)"
        )
    )

    return fig


def make_lag_fig(df):
    d = _prepare(df)
    results = []

    for borough, group in d.groupby("borough"):
        group = (
            group.sort_values("date")
            .set_index("date")
            .asfreq("MS")
        )

        for lag in range(-3, 4):
            paired = pd.DataFrame({
                "housing": group["h_filings_total"].shift(lag),
                "sirta": group["t_crashes"]
            }).dropna()

            corr = np.nan
            if (
                len(paired) >= 6
                and paired["housing"].nunique() > 1
                and paired["sirta"].nunique() > 1
            ):
                corr = paired["housing"].corr(paired["sirta"])

            results.append({
                "borough": borough,
                "lag_months": lag,
                "correlation": corr,
                "observations": len(paired)
            })

    lag_df = pd.DataFrame(results)

    fig = px.line(
        lag_df,
        x="lag_months",
        y="correlation",
        color="borough",
        markers=True,
        hover_data=["observations"],
        title="Q5: Housing–SIRTA Monthly Lag Correlations",
        labels={
            "lag_months": "Housing lag in months",
            "correlation": "Pearson correlation"
        },
        height=450
    )
    fig.add_hline(y=0, line_dash="dash")
    fig.update_xaxes(dtick=1)
    fig.update_yaxes(range=[-1, 1])
    return fig
