"""Q4 (Member 2): Do construction-heavy ZIPs have a higher share of crashes at
repeat-danger locations?

Chart: violin plot (with an inner box) of t_repeat_location_crashes / t_crashes per ZIP,
by construction tier (same tier function as Q11 and Q3).

A crash is at a repeat location when similar_fatalities_severe is at least 1 (see
DATA_CONTRACT section 7). Where that field is empty (about 10.5% of crashes) the flag is
unknown and is NOT counted as a repeat location, so the shares are lower bounds.

Usage in the app (table: zip_year, already filtered by src/filters.py):
    q04.make_fig(T["zip_year"], h)   # h = the Housing measure dropdown
    q04.make_caption()               # text for the card's hint
The Crash measure dropdown is not used: Q4 is always about repeat-location crashes.
"""
import pandas as pd
import plotly.express as px

from src.charts.tier_share import (DEFAULT_METRIC, MIN_CRASHES, TIER_COLORS, TIERS,
                                   empty_figure, metric_label, tier_labels, zip_shares)

NUMERATOR = "t_repeat_location_crashes"


def make_fig(df: pd.DataFrame, metric: str = DEFAULT_METRIC, min_crashes: int = MIN_CRASHES):
    """Violin plot: share of crashes at repeat locations, one point per ZIP, by tier."""
    shares = zip_shares(df, NUMERATOR, metric, min_crashes)
    if shares.empty:
        return empty_figure(f"No ZIP has at least {min_crashes} crashes for these filters.")
    shares, order = tier_labels(shares, NUMERATOR)

    fig = px.violin(
        shares, x="tier_label", y="share", color="construction_tier", box=True, points="all",
        category_orders={"tier_label": order, "construction_tier": TIERS},
        color_discrete_map=TIER_COLORS,
        hover_name="zip",
        hover_data={"borough": True, "t_crashes": True, "t_repeat_location_crashes": True,
                    "share": ":.1%", "tier_label": False, "construction_tier": False},
        labels={"tier_label": f"Construction tier of the ZIP ({metric_label(metric)})",
                "share": "Share of crashes at repeat locations", "t_crashes": "Crashes",
                "t_repeat_location_crashes": "Repeat-location crashes", "borough": "Borough"},
    )
    fig.update_traces(meanline_visible=True)
    fig.update_layout(
        template="plotly_white", height=460, showlegend=False,
        title="Share of serious crashes at repeat-danger locations, by construction tier"
              f"<br><sup>One point per ZIP with at least {min_crashes} crashes</sup>",
        yaxis_tickformat=".0%")
    return fig


def make_caption(min_crashes: int = MIN_CRASHES) -> str:
    """Caption that states what the share means and where it is limited."""
    return (
        "Each dot is a ZIP code. A crash counts as a repeat-danger location when similar severe "
        "or fatal crashes happened there before. That field is empty for about 10.5% of crashes; "
        "they are not counted as repeat locations, so the shares are lower bounds. Only crashes "
        f"with a ZIP are used, and a ZIP needs at least {min_crashes} crashes to appear. Tiers are "
        "thirds of the ZIPs shown, by the selected housing measure; many ZIPs have none, so the "
        "Low tier can be larger than a third. Associations, not causes: busy ZIPs have more of "
        "everything. This chart ignores the Crash measure.")
