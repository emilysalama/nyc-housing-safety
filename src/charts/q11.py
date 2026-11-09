"""Q11 (Member 6): Do serious crashes in construction-heavy ZIPs occur at different
hours than in quiet ZIPs?

Chart: hour-by-weekday heatmaps, one panel per construction tier (Low, Medium,
High). Each panel shows the share (%) of that group's own crashes, so groups with
different crash totals can be compared fairly.

Unlike most charts, Q11 needs row-level crashes AND the ZIP-year table (to rank
ZIPs by construction). So the app calls prepare() first, then make_fig():

    from src.charts import q11
    tiered = q11.prepare(crash_df, zip_year_df, metric="h_new_building")
    fig = q11.make_fig(tiered)


Both inputs should already be filtered by the shared filter (borough, year).
Uses only crashes that have a ZIP (original or recovered); see DATA_CONTRACT.md.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

HOURS = list(range(24))
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TIER_ORDER = ["Low", "Medium", "High"]


def assign_construction_tier(zip_year_df: pd.DataFrame, metric: str = "h_new_building") -> pd.Series:
    """Split ZIPs into Low / Medium / High thirds by their total `metric` in the data given.

    Each ZIP is placed by the share of ZIPs with a strictly smaller total. ZIPs with the
    same total therefore always share a tier (ranking with method="first" would split
    ties by ZIP order, which follows geography). With many ties the tiers can differ in
    size, and a tier can even be empty when most ZIPs have the same total.
    Returns a Series indexed by zip with values Low / Medium / High.
    """
    totals = zip_year_df.groupby("zip")[metric].sum()
    share_below = (totals.rank(method="min") - 1) / len(totals)
    tiers = pd.cut(share_below, bins=[0, 1 / 3, 2 / 3, 1], right=False, labels=TIER_ORDER)
    return tiers.astype(str).rename("construction_tier")



def prepare(crash_df: pd.DataFrame, zip_year_df: pd.DataFrame,
            metric: str = "h_new_building", street_only: bool = True) -> pd.DataFrame:
    """Attach each crash's ZIP construction tier.

    Drops crashes without a ZIP, hour or weekday, and keeps only crashes from the years
    present in zip_year_df (2022 to 2025). street_only=True also drops highway crashes
    (agreed default outcome, DATA_CONTRACT D1).
    """
    crashes = crash_df.dropna(subset=["zip", "crash_hour", "crash_weekday"]).copy()
    if street_only and "is_highway" in crashes.columns:
        crashes = crashes[~crashes["is_highway"].fillna(False).astype(bool)]
    # Use only the years in the ZIP-year table (the complete years 2022 to 2025,
    # DATA_CONTRACT section 2); 2026 is a partial year and is not in that table.
    crashes = crashes[crashes["year"].isin(zip_year_df["year"].unique())]
    tiers = assign_construction_tier(zip_year_df, metric)
    crashes["zip"] = crashes["zip"].astype(str)
    tier_table = tiers.rename_axis("zip").reset_index()
    tier_table["zip"] = tier_table["zip"].astype(str)
    return crashes.merge(tier_table, on="zip", how="inner")


def _weekday_names(series: pd.Series) -> pd.Series:
    """Accept weekday names or numbers (0 = Monday) and return names."""
    if pd.api.types.is_numeric_dtype(series):
        return series.map(dict(enumerate(WEEKDAYS)))
    return series.astype(str).str.strip().str.capitalize()


def _heatmap_matrices(df: pd.DataFrame):
    """For each tier return (counts, shares): weekday rows by hour columns."""
    weekday = _weekday_names(df["crash_weekday"])
    matrices = {}
    for tier in TIER_ORDER:
        mask = df["construction_tier"] == tier
        counts = (pd.crosstab(weekday[mask], df.loc[mask, "crash_hour"].astype(int))
                  .reindex(index=WEEKDAYS, columns=HOURS, fill_value=0))
        total = counts.to_numpy().sum()
        shares = counts / total * 100 if total else counts.astype(float)
        matrices[tier] = (counts, shares, int(total))
    return matrices


def make_fig(df: pd.DataFrame, metric_label: str = "new-building filings") -> go.Figure:
    """Hour-by-weekday heatmaps per construction tier. `df` comes from prepare()."""
    needed = {"construction_tier", "crash_hour", "crash_weekday"}
    if not needed.issubset(df.columns):
        raise ValueError("Missing columns " + str(sorted(needed - set(df.columns)))
                         + ". Call q11.prepare(crash_df, zip_year_df) first.")

    matrices = _heatmap_matrices(df)
    zmax = max(float(s.to_numpy().max()) for _, s, _ in matrices.values())

    titles = [f"{t} (n={matrices[t][2]:,})" for t in TIER_ORDER]
    fig = make_subplots(rows=1, cols=3, subplot_titles=titles, shared_yaxes=True,
                        horizontal_spacing=0.03)

    for col, tier in enumerate(TIER_ORDER, start=1):
        counts, shares, _ = matrices[tier]
        fig.add_trace(go.Heatmap(
            z=shares.to_numpy(), x=HOURS, y=WEEKDAYS, customdata=counts.to_numpy(),
            zmin=0, zmax=zmax, colorscale="YlOrRd",
            showscale=(col == 3), colorbar=dict(title="% of group's crashes"),
            hovertemplate=("%{y}, %{x}:00<br>%{z:.2f}% of this group's crashes"
                           "<br>%{customdata} crashes<extra>" + tier + "</extra>"),
        ), row=1, col=col)
        fig.update_xaxes(title_text="Hour of day", dtick=3, row=1, col=col)

    fig.update_yaxes(autorange="reversed")  # Monday at the top
    fig.update_layout(
        title=dict(text="When do serious crashes happen? Hour and weekday, by how much "
                        "construction the ZIP has",
                   x=0.01),
        height=560, margin=dict(t=100, b=145, l=70, r=50),
        annotations=list(fig.layout.annotations) + [dict(
             text=("Each panel shows the share of that group's own crashes. ZIPs are split into "
                  f"thirds by {metric_label} in the selected data.<br>Crashes with a ZIP "
                  "only; highway crashes excluded by default; association, not causation."),
            x=0, y=-0.16, xref="paper", yref="paper", showarrow=False, xanchor="left",
            font=dict(size=11))],
    )
    return fig
