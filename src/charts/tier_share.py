"""Shared helper for Q3 and Q4 (Member 2).

Both questions ask whether a share of serious crashes (fatal, repeat-location) differs
between ZIPs with little and a lot of construction. They must use the same tier
definition as Q11, so the tier comes from assign_construction_tier in src/charts/q11.py
and follows the same housing measure (the app's "Housing measure" dropdown).

Unit of analysis: one row per ZIP, pooled over the years present in the dataframe that is
passed in. A share needs enough crashes behind it, so ZIPs with fewer than MIN_CRASHES
crashes are left out of the chart (a share of 1 fatal crash out of 2 is mostly noise).
"""
import pandas as pd
import plotly.graph_objects as go

from src.charts.q11 import assign_construction_tier

TIERS = ["Low", "Medium", "High"]  # same labels and order as q11.assign_construction_tier
TIER_COLORS = {"Low": "#4c9be8", "Medium": "#f2a541", "High": "#d9534f"}
MIN_CRASHES = 10
DEFAULT_METRIC = "h_new_building"
BAD_METRIC = "h_median_days_permit_to_signoff"  # a median cannot be summed into tiers (as in app.py)


def metric_label(metric: str) -> str:
    """'h_new_building' -> 'new building' (for axis titles)."""
    return metric[2:].replace("_", " ")


def zip_shares(df: pd.DataFrame, numerator: str, metric: str = DEFAULT_METRIC,
               min_crashes: int = MIN_CRASHES) -> pd.DataFrame:
    """One row per ZIP with its construction tier and share = numerator / t_crashes.

    `df` is a (filtered) ZIP-by-year table with the contract's column names.
    The tier is set on the rows given, so a Borough or Year filter changes the tiers,
    exactly as it does in Q11. Tiers are set BEFORE the minimum-crash rule is applied,
    so ZIPs with few crashes still count when the construction thirds are drawn.
    """
    columns = ["zip", "borough", "t_crashes", numerator, "construction_tier", "share"]
    if df.empty:
        return pd.DataFrame(columns=columns)
    if metric == BAD_METRIC:
        metric = DEFAULT_METRIC

    df = df.assign(zip=df["zip"].astype(str))
    per_zip = df.groupby(["zip", "borough"], as_index=False)[["t_crashes", numerator]].sum()
    per_zip["construction_tier"] = per_zip["zip"].map(assign_construction_tier(df, metric))

    per_zip = per_zip[per_zip["t_crashes"] >= min_crashes].copy()
    per_zip["share"] = per_zip[numerator] / per_zip["t_crashes"]
    return per_zip[columns]


def tier_labels(per_zip: pd.DataFrame, numerator: str):
    """Add an axis label per tier that shows how many ZIPs and the pooled share.

    The pooled share is total events / total crashes in the tier, so large ZIPs weigh more
    than in the box plot (where every ZIP counts once). Showing both avoids a misleading read.
    Returns the dataframe with a `tier_label` column and the labels in Low, Medium, High order.
    """
    pooled = per_zip.groupby("construction_tier").agg(
        zips=("zip", "nunique"), crashes=("t_crashes", "sum"), events=(numerator, "sum"))
    labels = {}
    for tier in TIERS:
        if tier in pooled.index:
            row = pooled.loc[tier]
            labels[tier] = f"{tier}<br>{int(row.zips)} ZIPs, pooled {row.events / row.crashes:.1%}"
    per_zip = per_zip[per_zip["construction_tier"].isin(labels)].copy()
    per_zip["tier_label"] = per_zip["construction_tier"].map(labels)
    return per_zip, [labels[t] for t in TIERS if t in labels]


def empty_figure(message: str) -> go.Figure:
    """A blank figure with a message, for filters that leave too little data."""
    fig = go.Figure()
    fig.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(template="plotly_white", height=420)
    return fig
