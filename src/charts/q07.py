"""Q7: Is the construction-crash link stable from 2022 to 2025?
Table: zip_year. Chart: Spearman correlation heatmap, borough x year."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

MIN_ZIPS = 5  # a correlation on fewer ZIPs is too noisy to show


def spearman(x: pd.Series, y: pd.Series) -> float:
    """Spearman = Pearson on ranks (avoids a scipy dependency)."""
    return x.rank().corr(y.rank())


def make_fig(df, housing_col="h_new_building", transport_col="t_crashes_street"):
    rows = []
    for (borough, year), g in df.groupby(["borough", "year"]):
        rho = spearman(g[housing_col], g[transport_col]) if len(g) >= MIN_ZIPS else float("nan")
        rows.append({"borough": borough, "year": year, "rho": rho})
    corr = pd.DataFrame(rows)
    if corr.empty:
        return px.imshow([[0]], title="No data for the selected filters")
    grid = corr.pivot(index="borough", columns="year", values="rho")

    # D4: does the result change without 2025? Compare mean rho with and without it.
    # Years with no valid correlation (NaN) are named, so a missing year is never hidden.
    all_mean = corr["rho"].mean()
    no25_mean = corr.loc[corr["year"] != 2025, "rho"].mean()
    empty_years = sorted(corr.groupby("year")["rho"].apply(lambda r: r.isna().all()).loc[lambda m: m].index)
    caption = f"Mean rho all years: {all_mean:.2f}; excluding 2025: {no25_mean:.2f}. Association only, not causation."
    if empty_years:
        caption = (f"No valid correlation for {', '.join(map(str, empty_years))} "
                   f"(too few ZIPs or no variation), so those years are not in the means. " + caption)
    fig = px.imshow(grid, zmin=-1, zmax=1, color_continuous_scale="RdBu_r", text_auto=".2f",
                    aspect="auto", labels=dict(x="Year", y="Borough", color="Spearman rho"),
                    title=f"Spearman correlation across ZIPs: {housing_col} vs {transport_col}")
    fig.update_xaxes(type="category")
    fig.add_annotation(xref="paper", yref="paper", x=0, y=-0.18, showarrow=False, align="left",
                       text=caption)
    return fig


def make_coverage_fig(path="data/clean/coverage_report.csv"):
    cov = pd.read_csv(path)
    cov["group"] = cov["group"].astype(str)

    parts = [("year", None),
             ("is_highway", {"highway": "Highway", "street": "Street"}),
             ("fatal_status", {"fatal": "Fatal", "nonfatal": "Non-fatal"})]
    frames = []
    for dim, names in parts:
        d = cov[cov["dimension"] == dim].copy()
        if names:
            d["group"] = d["group"].map(names)
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)

    fig = go.Figure()
    for col, label in [("original_pct", "Original ZIP"),
                       ("spatial_join_pct", "Recovered by spatial join"),
                       ("missing_pct", "Missing (excluded)")]:
        fig.add_bar(x=d["group"], y=d[col], name=label,
                    text=d[col].round(1).astype(str) + "%", textposition="inside")
    fig.update_layout(barmode="stack",
                      title=dict(text="Q7 data coverage: where each crash's ZIP came from", y=0.95),
                      yaxis_title="% of crashes", xaxis_title="", yaxis_range=[0, 100],
                      height=720, margin=dict(t=130, b=240, l=70, r=40),
                      legend=dict(orientation="h", x=0, y=1.02, xanchor="left", yanchor="bottom",
                                  entrywidthmode="pixels", entrywidth=230))
    fig.update_xaxes(type="category")
    ov = cov[cov["dimension"] == "overall"].iloc[0]
    fat = cov[(cov["dimension"] == "fatal_status") & (cov["group"] == "fatal")].iloc[0]
    non = cov[(cov["dimension"] == "fatal_status") & (cov["group"] == "nonfatal")].iloc[0]
    fig.add_annotation(
        xref="paper", yref="paper", x=0, y=-0.12, yanchor="top", showarrow=False, align="left",
        text=(f"{ov['missing_pct']:.1f}% of {int(ov['total_crashes']):,} crashes have no ZIP.<br>"
              f"Fatal crashes: {fat['missing_pct']:.1f}% missing vs {non['missing_pct']:.1f}% for non-fatal.<br>"
              f"Dropped: {int(ov['housing_rows_dropped_zip_year'])} housing and "
              f"{int(ov['crash_rows_dropped_zip_year'])} crash ZIP-year rows; "
              f"{int(ov['unverified_zip_10000_crashes'])} crashes have an unverified ZIP (10000)."))
    return fig