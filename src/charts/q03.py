"""Q3 (Member 2): Are crashes in construction-heavy ZIPs more likely to be fatal?

Chart: box plot of t_fatal_crashes / t_crashes per ZIP, by construction tier (Low, Medium,
High, from the same function as Q11). Per DATA_CONTRACT decision D3, the figure comes with
a caption that reports the share of fatal crashes that have no ZIP (from coverage_report.csv)
and with a borough-level check, because those crashes are missing from the ZIP table.

Usage in the app (table: zip_year, already filtered by src/filters.py):
    q03.make_fig(T["zip_year"], h)           # h = the Housing measure dropdown
    q03.make_borough_fig(T["zip_year"], h)   # the borough check
    q03.make_caption()                       # text for the card's hint
The Crash measure dropdown is not used: Q3 is always about fatal crashes.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px

from src.charts.tier_share import (DEFAULT_METRIC, MIN_CRASHES, TIER_COLORS, TIERS,
                                   empty_figure, metric_label, tier_labels, zip_shares)

NUMERATOR = "t_fatal_crashes"
COVERAGE_PATH = Path(__file__).resolve().parents[2] / "data" / "clean" / "coverage_report.csv"


def make_fig(df: pd.DataFrame, metric: str = DEFAULT_METRIC, min_crashes: int = MIN_CRASHES):
    """Box plot: share of crashes that are fatal, one point per ZIP, grouped by tier."""
    shares = zip_shares(df, NUMERATOR, metric, min_crashes)
    if shares.empty:
        return empty_figure(f"No ZIP has at least {min_crashes} crashes for these filters.")
    shares, order = tier_labels(shares, NUMERATOR)

    fig = px.box(
        shares, x="tier_label", y="share", color="construction_tier", points="all",
        category_orders={"tier_label": order, "construction_tier": TIERS},
        color_discrete_map=TIER_COLORS,
        hover_name="zip",
        hover_data={"borough": True, "t_crashes": True, "t_fatal_crashes": True,
                    "share": ":.1%", "tier_label": False, "construction_tier": False},
        labels={"tier_label": f"Construction tier of the ZIP ({metric_label(metric)})",
                "share": "Share of crashes that are fatal", "t_crashes": "Crashes",
                "t_fatal_crashes": "Fatal crashes", "borough": "Borough"},
    )
    fig.update_traces(boxmean=True)  # dashed line = mean, solid line = median
    fig.update_layout(
        template="plotly_white", height=460, showlegend=False,
        title="Share of serious crashes that are fatal, by construction tier"
              f"<br><sup>One point per ZIP with at least {min_crashes} crashes</sup>",
        yaxis_tickformat=".0%")
    return fig


def make_borough_fig(df: pd.DataFrame, metric: str = DEFAULT_METRIC, min_crashes: int = MIN_CRASHES):
    """Check (decision D3): the same question inside each borough.

    The citywide chart mixes boroughs that differ in many ways. Here the fatal share is
    pooled per borough and tier (total fatal crashes / total crashes of its ZIPs).
    """
    shares = zip_shares(df, NUMERATOR, metric, min_crashes)
    if shares.empty:
        return empty_figure(f"No ZIP has at least {min_crashes} crashes for these filters.")

    grouped = shares.groupby(["borough", "construction_tier"], as_index=False).agg(
        zips=("zip", "nunique"), crashes=("t_crashes", "sum"), fatal=(NUMERATOR, "sum"))
    grouped["share"] = grouped["fatal"] / grouped["crashes"]

    fig = px.bar(
        grouped, x="borough", y="share", color="construction_tier", barmode="group",
        category_orders={"construction_tier": TIERS}, color_discrete_map=TIER_COLORS,
        hover_data={"zips": True, "crashes": True, "fatal": True, "share": ":.1%"},
        labels={"share": "Share of crashes that are fatal", "borough": "Borough",
                "construction_tier": "Construction tier", "zips": "ZIPs",
                "crashes": "Crashes", "fatal": "Fatal crashes"})
    fig.update_layout(
        template="plotly_white", height=420, yaxis_tickformat=".0%",
        title="The same comparison inside each borough"
              "<br><sup>Pooled share per borough and tier; few ZIPs in a group means a noisy bar</sup>")
    return fig


def make_caption(coverage_path: Path = COVERAGE_PATH) -> str:
    """Caption required by decision D3, with the numbers read from coverage_report.csv."""
    try:
        cov = pd.read_csv(coverage_path)
        fatal = cov[(cov["dimension"] == "fatal_status") & (cov["group"] == "fatal")].iloc[0]
        nonfatal = cov[(cov["dimension"] == "fatal_status") & (cov["group"] == "nonfatal")].iloc[0]
        boroughs = cov[(cov["dimension"] == "borough") & (cov["group"] != "missing")]
        low = boroughs.loc[boroughs["fatal_crashes_missing_zip_pct"].idxmin()]
        high = boroughs.loc[boroughs["fatal_crashes_missing_zip_pct"].idxmax()]
        coverage = (
            f"{int(fatal.fatal_crashes_missing_zip)} of {int(fatal.fatal_crashes)} fatal crashes "
            f"({fatal.fatal_crashes_missing_zip_pct:.1f}%) have no ZIP, against "
            f"{nonfatal.missing_pct:.1f}% of non-fatal crashes, so fatal shares by ZIP are "
            f"underestimates. The loss differs by borough, from "
            f"{low.fatal_crashes_missing_zip_pct:.0f}% ({low.group}) to "
            f"{high.fatal_crashes_missing_zip_pct:.0f}% ({high.group}).")
    except (FileNotFoundError, KeyError, IndexError, ValueError):
        coverage = "Many fatal crashes have no ZIP (see coverage_report.csv), so fatal shares by ZIP are underestimates."
    return (
        "Each dot is a ZIP code. Only crashes that have a ZIP are used. " + coverage +
        " Tiers are thirds of the ZIPs shown, by the selected housing measure; many ZIPs have "
        "none, so the Low tier can be larger than a third. Associations, not causes: busy "
        "ZIPs have more of everything. This chart ignores the Crash measure.")
