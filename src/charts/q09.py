"""Q9: Where do high-construction and high-crash ZIPs overlap?
Table: zip_year. Chart: bivariate choropleth (3 construction tiers x 3 crash tiers)."""
import json
from functools import lru_cache
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

GEOJSON_PATH = Path(__file__).resolve().parents[2] / "data" / "clean" / "nyc_zip_boundaries.geojson"
ZIP_KEY = "properties.zcta5"                      # team rule: ZIP property in the shared boundary file
MEDIAN_COL = "h_median_days_permit_to_signoff"    # a median cannot be summed across years
TIER_NAMES = ["low", "medium", "high"]
NO_DATA = "#F2E6B8"  # pale yellow: clearly not part of the bivariate palette
# Stevens' 3x3 bivariate palette: (crash tier, construction tier) -> colour.
# Construction runs teal (left to right), crashes run purple (bottom to top); dark blue = high on both.
PALETTE = {
    (0, 0): "#d9d9d9", (0, 1): "#ace4e4", (0, 2): "#5ac8c8",
    (1, 0): "#dfb0d6", (1, 1): "#a5add3", (1, 2): "#5698b9",
    (2, 0): "#be64ac", (2, 1): "#8c62aa", (2, 2): "#3b4994",
}


def _group_name(crash_tier, construction_tier):
    return f"Construction {TIER_NAMES[construction_tier]}, crashes {TIER_NAMES[crash_tier]}"


COLOR_MAP = {_group_name(c, h): colour for (c, h), colour in PALETTE.items()} | {"No data": NO_DATA}


def _round_coords(coords):
    """Round polygon coordinates to 4 decimals (about 10 m) so the figure stays small."""
    if isinstance(coords[0], (int, float)):
        return [round(coords[0], 4), round(coords[1], 4)]
    return [_round_coords(c) for c in coords]


@lru_cache(maxsize=1)
def _load_features():
    """Read the shared boundary file once; return {5-digit zip: feature}."""
    with open(GEOJSON_PATH) as f:
        gj = json.load(f)
    features = {}
    for ft in gj["features"]:
        ft["geometry"]["coordinates"] = _round_coords(ft["geometry"]["coordinates"])
        features[str(ft["properties"]["zcta5"]).zfill(5)] = ft
    return features


def _tier(values):
    """0/1/2 = bottom/middle/top third by average rank. Tied values (e.g. many zeros) share one tier."""
    pct = values.rank(method="average", pct=True)
    return pd.cut(pct, [0, 1 / 3, 2 / 3, 1.0], labels=False, include_lowest=True)


def message_fig(text):
    fig = go.Figure()
    fig.add_annotation(text=text, showarrow=False, font=dict(size=14))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def make_fig(df, housing_col="h_new_building", transport_col="t_crashes_street"):
    if df.empty:
        return message_fig("No data for the selected filters")

    # One row per ZIP: counts are summed over the selected years; the median-days column is averaged.
    housing_agg = "mean" if housing_col == MEDIAN_COL else "sum"
    zips = (df.assign(zip=df["zip"].astype(str).str.zfill(5))
              .groupby(["zip", "borough"], as_index=False)
              .agg(h=(housing_col, housing_agg), t=(transport_col, "sum")))
    zips["h_tier"], zips["t_tier"] = _tier(zips["h"]), _tier(zips["t"])
    zips["group"] = [
        "No data" if pd.isna(h) or pd.isna(t) else _group_name(int(t), int(h))
        for h, t in zip(zips["h_tier"], zips["t_tier"])]

    features = _load_features()
    drawable = zips[zips["zip"].isin(features)]
    n_missing = len(zips) - len(drawable)
    if drawable.empty:
        return message_fig("No ZIP polygons match the selected data")
    geojson = {"type": "FeatureCollection", "features": [features[z] for z in drawable["zip"]]}

    # Centre and zoom on the ZIPs shown (centlat/centlon are strings like "+40.69")
    lats = [float(features[z]["properties"]["centlat"]) for z in drawable["zip"]]
    lons = [float(features[z]["properties"]["centlon"]) for z in drawable["zip"]]
    zoom = 9.4 if max(lats) - min(lats) > 0.25 else 10.9

    fig = px.choropleth_map(
        drawable, geojson=geojson, locations="zip", featureidkey=ZIP_KEY,
        color="group", color_discrete_map=COLOR_MAP, opacity=0.85,
        hover_name="zip", hover_data={"borough": True, "h": ":,.0f", "t": ":,.0f", "group": True, "zip": False},
        labels={"h": housing_col, "t": transport_col, "group": "Group"},
        map_style="carto-positron", center={"lat": sum(lats) / len(lats), "lon": sum(lons) / len(lons)},
        zoom=zoom, title=f"Where construction and crashes overlap: {housing_col} x {transport_col}")
    fig.update_layout(showlegend=False)

    # 3x3 legend on a white card so it stays readable over map labels
    x0, y0, w, h = 0.06, 0.12, 0.03, 0.055
    fig.add_shape(type="rect", xref="paper", yref="paper", layer="above",
                  x0=x0 - 0.05, x1=x0 + 3 * w + 0.012, y0=y0 - 0.07, y1=y0 + 3 * h + 0.025,
                  fillcolor="white", opacity=0.9, line=dict(color="#E3E8EE", width=1))
    for (c, k), colour in PALETTE.items():
        fig.add_shape(type="rect", xref="paper", yref="paper", layer="above",
                      x0=x0 + k * w, x1=x0 + (k + 1) * w, y0=y0 + c * h, y1=y0 + (c + 1) * h,
                      fillcolor=colour, line=dict(color="white", width=1))
    fig.add_annotation(xref="paper", yref="paper", x=x0 + 1.5 * w, y=y0 - 0.01, yanchor="top",
                       showarrow=False, text="Construction \u2192", font=dict(size=11))
    fig.add_annotation(xref="paper", yref="paper", x=x0 - 0.008, y=y0 + 1.5 * h, xanchor="right",
                       textangle=-90, showarrow=False, text="Crashes \u2192", font=dict(size=11))

    plural = "s" if n_missing != 1 else ""
    no_data_note = " Pale yellow = no value for this measure." if (drawable["group"] == "No data").any() else ""
    fig.add_annotation(
        xref="paper", yref="paper", x=0, y=-0.08, showarrow=False, align="left",
        text=(f"Tiers are thirds of the {len(drawable)} ZIPs shown, so they shift with the Borough and Year filters. "
              f"{n_missing} ZIP{plural} without a boundary polygon {'are' if n_missing != 1 else 'is'} not drawn."
              f"{no_data_note} Association only, not causation."))
    return fig
