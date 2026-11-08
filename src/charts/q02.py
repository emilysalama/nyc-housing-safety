"""Q2: Are serious crashes closer to new-building sites than
to demolition sites?

Inputs:
- crashes: row-level serious crashes
- sites: New Building and Full Demolition site points

Chart:
- Grouped bars showing crash share by nearest-site distance band.
- Highway crashes are excluded.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.neighbors import BallTree


DISTANCE_BANDS = [
    "0–250 m",
    "250–500 m",
    "500 m–1 km",
    "Over 1 km"
]

SITE_TYPES = ["New Building", "Full Demolition"]

EARTH_RADIUS_M = 6371000


def message_fig(message):
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, font=dict(size=14))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def _nearest_distances(crashes, sites):
    """Return the distance in metres to each crash's nearest site."""

    crash_coords = np.radians(
        crashes[["latitude", "longitude"]].to_numpy(dtype=float)
    )

    site_coords = np.radians(
        sites[["latitude", "longitude"]].to_numpy(dtype=float)
    )

    tree = BallTree(site_coords, metric="haversine")
    distances, _ = tree.query(crash_coords, k=1)

    return distances[:, 0] * EARTH_RADIUS_M


def _distance_band(distance):
    if distance <= 250:
        return DISTANCE_BANDS[0]
    elif distance <= 500:
        return DISTANCE_BANDS[1]
    elif distance <= 1000:
        return DISTANCE_BANDS[2]
    return DISTANCE_BANDS[3]


def make_fig(df):
    """
    df must be a dictionary containing:
        df["crashes"]: row-level serious crashes
        df["sites"]: New Building and Full Demolition site points

    Borough and year filtering is handled by the dashboard before
    this function is called.
    """

    if not isinstance(df, dict) or "crashes" not in df or "sites" not in df:
        raise ValueError(
            'Pass a dictionary: {"crashes": crash_df, "sites": sites_df}'
        )

    crashes = df["crashes"].copy()
    sites = df["sites"].copy()

    required_crashes = {"latitude", "longitude", "is_highway"}
    required_sites = {"latitude", "longitude", "job_type"}

    if not required_crashes.issubset(crashes.columns):
        raise ValueError(
            f"Crashes are missing columns: "
            f"{sorted(required_crashes - set(crashes.columns))}"
        )

    if not required_sites.issubset(sites.columns):
        raise ValueError(
            f"Sites are missing columns: "
            f"{sorted(required_sites - set(sites.columns))}"
        )

    # Keep street crashes only. Unknown highway values are excluded.
    street_values = crashes["is_highway"].astype(str).str.strip().str.lower()
    crashes = crashes[street_values.isin(["false", "0", "no"])].copy()

    # Keep crashes with valid coordinates.
    crashes["latitude"] = pd.to_numeric(
        crashes["latitude"], errors="coerce"
    )
    crashes["longitude"] = pd.to_numeric(
        crashes["longitude"], errors="coerce"
    )

    crashes = crashes.dropna(
        subset=["latitude", "longitude"]
    ).copy()

    crashes = crashes[
        crashes["latitude"].between(40.4774, 40.9176)
        & crashes["longitude"].between(-74.2591, -73.7004)
    ].copy()

    # Keep valid site coordinates and required site types.
    sites["latitude"] = pd.to_numeric(
        sites["latitude"], errors="coerce"
    )
    sites["longitude"] = pd.to_numeric(
        sites["longitude"], errors="coerce"
    )

    sites = sites.dropna(
        subset=["latitude", "longitude", "job_type"]
    ).copy()

    sites = sites[
        sites["latitude"].between(40.4774, 40.9176)
        & sites["longitude"].between(-74.2591, -73.7004)
        & sites["job_type"].isin(SITE_TYPES)
    ].copy()

    if crashes.empty:
        return message_fig(
            "No eligible street crashes with valid NYC coordinates"
        )

    results = []

    for site_type in SITE_TYPES:
        type_sites = sites[sites["job_type"] == site_type]

        if type_sites.empty:
            return message_fig(
                f"No valid site coordinates found for {site_type}"
            )

        distances = _nearest_distances(crashes, type_sites)

        temp = pd.DataFrame({
            "site_type": site_type,
            "distance_m": distances
        })

        temp["distance_band"] = temp["distance_m"].apply(_distance_band)
        results.append(temp)

    result = pd.concat(results, ignore_index=True)

    counts = (
        result.groupby(["site_type", "distance_band"], observed=False)
        .size()
        .reset_index(name="crash_count")
    )

    totals = counts.groupby("site_type")["crash_count"].transform("sum")
    counts["crash_share"] = counts["crash_count"] / totals * 100

    counts["distance_band"] = pd.Categorical(
        counts["distance_band"],
        categories=DISTANCE_BANDS,
        ordered=True
    )

    fig = px.bar(
        counts,
        x="distance_band",
        y="crash_share",
        color="site_type",
        barmode="group",
        category_orders={"distance_band": DISTANCE_BANDS},
        hover_data={
            "crash_count": True,
            "crash_share": ":.2f"
        },
        labels={
            "distance_band": "Distance to nearest site",
            "crash_share": "Share of crashes (%)",
            "site_type": "Site type",
            "crash_count": "Number of crashes"
        },
        title=(
            "How close are serious street crashes to "
            "new-building and demolition sites?"
        )
    )

    fig.update_layout(
        height=520,
        margin=dict(t=80, b=115),
        legend_title_text="Site type",
        yaxis_ticksuffix="%",
        yaxis_rangemode="tozero"
    )

    fig.add_annotation(
        x=0,
        y=-0.25,
        xref="paper",
        yref="paper",
        text=(
            "Only serious street crashes with valid NYC coordinates are included; "
            "highway crashes are excluded. Each crash is compared with its "
            "nearest site of each type. Percentages are calculated separately "
            "for each site type and sum to 100%. Distances are straight-line "
            "distances, not road-network distances."
        ),
        showarrow=False,
        xanchor="left",
        align="left",
        font=dict(size=10)
    )

    return fig
