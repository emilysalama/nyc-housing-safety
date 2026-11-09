"""Q1: Do ZIPs with a surge in new-building filings see a rise
in serious street crashes the following year?

Uses:
- zip_year: ZIP-year housing and crash metrics
- borough_month: borough-month crash totals for location coverage

Construction change in year Y is compared with street-crash
change from year Y to Y+1.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


def message_fig(message):
    fig = go.Figure()
    fig.add_annotation(
        text=message, showarrow=False, font=dict(size=14)
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def _correlation(df):
    """Pearson correlation, when enough observations are available."""
    if len(df) < 2:
        return np.nan

    return df["construction_change"].corr(
        df["crash_change_next_year"]
    )


def _prepare(zip_year):
    required = {
        "zip", "year", "borough",
        "h_new_building", "t_crashes_street"
    }

    missing = required - set(zip_year.columns)
    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    data = zip_year.copy()

    data["zip"] = (
        data["zip"].astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(5)
    )

    for col in [
        "year", "h_new_building", "t_crashes_street"
    ]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.dropna(
        subset=[
            "zip", "year", "borough",
            "h_new_building", "t_crashes_street"
        ]
    )

    yearly = (
        data.groupby(
            ["zip", "borough", "year"], as_index=False
        )
        .agg(
            new_buildings=("h_new_building", "sum"),
            crashes=("t_crashes_street", "sum")
        )
    )

    yearly = yearly.sort_values(["zip", "year"])

    # Change in new-building filings from previous year to year Y.
    yearly["construction_change"] = (
        yearly.groupby("zip")["new_buildings"].diff()
    )

    # Obtain the following year's crash count.
    next_year = yearly[
        ["zip", "borough", "year", "crashes"]
    ].copy()

    next_year["year"] = next_year["year"] - 1
    next_year = next_year.rename(
        columns={"crashes": "following_year_crashes"}
    )

    plot_data = yearly.merge(
        next_year,
        on=["zip", "borough", "year"],
        how="inner"
    )

    # Change in street crashes from Y to Y+1.
    plot_data["crash_change_next_year"] = (
        plot_data["following_year_crashes"]
        - plot_data["crashes"]
    )

    plot_data["outcome_year"] = plot_data["year"] + 1

    plot_data = plot_data.dropna(
        subset=[
            "construction_change",
            "crash_change_next_year"
        ]
    )

    return plot_data


def _coverage(zip_year, borough_month, borough=None):
    """Calculate the share of street crashes represented in ZIP data."""

    zy = zip_year.copy()
    bm = borough_month.copy()

    if borough not in (None, "All"):
        zy = zy[zy["borough"] == borough]
        bm = bm[bm["borough"] == borough]

    zip_counts = (
        zy.groupby("year")["t_crashes_street"].sum()
    )

    total_counts = (
        bm.groupby("year")["t_crashes_street"].sum()
    )

    coverage = pd.concat(
        [
            zip_counts.rename("with_zip"),
            total_counts.rename("all_crashes")
        ],
        axis=1
    ).fillna(0)

    coverage["coverage_pct"] = np.where(
        coverage["all_crashes"] > 0,
        coverage["with_zip"] / coverage["all_crashes"] * 100,
        np.nan
    )

    return coverage.reset_index()


def make_fig(tables, borough="All", selected_year="All"):
    """
    tables must contain:
        tables["zip_year"]
        tables["borough_month"]

    selected_year refers to the construction-change year.
    """

    if not isinstance(tables, dict):
        raise ValueError(
            "Q1 requires a dictionary with zip_year and borough_month."
        )

    if "zip_year" not in tables or "borough_month" not in tables:
        raise ValueError(
            "Q1 requires zip_year and borough_month datasets."
        )

    zip_year = tables["zip_year"].copy()
    borough_month = tables["borough_month"].copy()

    # Apply borough selection but retain every year for the lag.
    if borough not in (None, "All"):
        zip_year = zip_year[
            zip_year["borough"] == borough
        ]

    plot_data = _prepare(zip_year)

    if plot_data.empty:
        return message_fig(
            "Not enough consecutive years to calculate changes."
        )

    # Apply the selected construction-change year AFTER calculating lags.
    if selected_year not in (None, "All"):
        plot_data = plot_data[
            plot_data["year"] == int(selected_year)
        ]

    if plot_data.empty:
        return message_fig(
            "No valid following-year comparison for this selected year. "
            "Available construction-change years are 2023 and 2024."
        )

    # D4: compare the full result with the result excluding 2025 outcomes.
    all_corr = _correlation(plot_data)

    without_2025 = plot_data[
        plot_data["outcome_year"] != 2025
    ]

    no_2025_corr = _correlation(without_2025)

    def corr_text(value):
        return "not available" if pd.isna(value) else f"{value:.3f}"

    # D4: annual ZIP location coverage.
    coverage = _coverage(
        zip_year,
        borough_month,
        borough=borough
    )

    coverage["year"] = coverage["year"].astype(int)
    coverage = coverage.sort_values("year")

    coverage_labels = [
        f"{int(row.year)}: {row.coverage_pct:.1f}%"
        if pd.notna(row.coverage_pct)
        else f"{int(row.year)}: unavailable"
        for row in coverage.itertuples()
    ]

    coverage_text = (
        "<br>".join(coverage_labels)
        if coverage_labels
        else "Location coverage unavailable"
    )

    # Build scatter chart and a coverage table beside it.
    fig = make_subplots(
        rows=1,
        cols=2,
        specs=[[{"type": "xy"}, {"type": "table"}]],
        column_widths=[0.76, 0.24],
        horizontal_spacing=0.07,
        subplot_titles=[
            "Construction change vs. following-year crash change",
            "ZIP location coverage"
        ]
    )

    scatter = px.scatter(
        plot_data,
        x="construction_change",
        y="crash_change_next_year",
        color="borough",
        hover_data={
            "zip": True,
            "year": True,
            "outcome_year": True,
            "construction_change": True,
            "crash_change_next_year": True
        },
        labels={
            "construction_change": "Change in new-building filings",
            "crash_change_next_year": "Following-year change in street crashes",
            "borough": "Borough"
        },
        opacity=0.75
    )

    for trace in scatter.data:
        fig.add_trace(trace, row=1, col=1)

    fig.add_hline(
        y=0, line_dash="dash", line_color="gray",
        row=1, col=1
    )
    fig.add_vline(
        x=0, line_dash="dash", line_color="gray",
        row=1, col=1
    )

    fig.add_trace(
        go.Table(
            header=dict(
                values=["Year", "Coverage"],
                align="center"
            ),
            cells=dict(
                values=[
                    coverage["year"].tolist(),
                    [
                        f"{v:.1f}%" if pd.notna(v) else "N/A"
                        for v in coverage["coverage_pct"]
                    ]
                ],
                align="center"
            )
        ),
        row=1,
        col=2
    )

    fig.update_layout(
        title=(
            "Do new-building surges precede increases in "
            "serious street crashes?"
        ),
        height=600,
        margin=dict(t=100, b=145, l=65, r=30),
        legend_title_text="Borough"
    )

    fig.update_xaxes(
        title_text="Change in new-building filings",
        row=1, col=1
    )

    fig.update_yaxes(
        title_text="Following-year change in serious street crashes",
        row=1, col=1
    )

    comparison_text = (
        f"Pearson correlation — all included outcomes: "
        f"{corr_text(all_corr)}"
        f"<br>Pearson correlation — excluding 2025 outcomes: "
        f"{corr_text(no_2025_corr)}"
        f"<br>Points: {len(plot_data):,}; "
        f"construction-change years: "
        f"{', '.join(map(str, sorted(plot_data['year'].unique())))}"
    )

    fig.add_annotation(
        x=0, y=-0.24,
        xref="paper", yref="paper",
        text=(
            comparison_text
            + "<br>Coverage = ZIP-linked street crashes / all borough-month "
            "street crashes. Construction change in year Y is compared "
            "with crash change from Y to Y+1. Association does not imply causation."
        ),
        showarrow=False,
        xanchor="left",
        align="left",
        font=dict(size=10)
    )

    return fig
