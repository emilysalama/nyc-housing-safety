"""Q7: Is the construction-crash link stable from 2022 to 2025?
Table: zip_year. Chart: Spearman correlation heatmap, borough x year."""
import pandas as pd
import plotly.express as px

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
    all_mean = corr["rho"].mean()
    no25_mean = corr.loc[corr["year"] != 2025, "rho"].mean()
    fig = px.imshow(grid, zmin=-1, zmax=1, color_continuous_scale="RdBu_r", text_auto=".2f",
                    aspect="auto", labels=dict(x="Year", y="Borough", color="Spearman rho"),
                    title=f"Spearman correlation across ZIPs: {housing_col} vs {transport_col}")
    fig.update_xaxes(type="category")
    fig.add_annotation(xref="paper", yref="paper", x=0, y=-0.18, showarrow=False, align="left",
                       text=f"Mean rho all years: {all_mean:.2f}; excluding 2025: {no25_mean:.2f}. "
                            f"Association only, not causation.")
    return fig
