"""Q6: ZIP-level Housing and SIRTA regression residuals."""
import numpy as np
import pandas as pd
import plotly.express as px


def make_fig(df):
    d = df.copy()
    if d.empty:
        raise ValueError("No ZIP-year data for these filters.")

    d = d[d["year"].between(2022, 2025)].copy()

    for col in ("h_filings_total", "t_crashes"):
        d[col] = pd.to_numeric(d[col], errors="coerce").fillna(0)

    if d.empty:
        raise ValueError("No complete-year records available.")

    # The website year filter may select just one year.
    # Use the number of selected months, not always 48.
    months = 12 * d["year"].nunique()

    z = d.groupby("zip", as_index=False).agg(
        housing_filings=("h_filings_total", "sum"),
        sirta_crashes=("t_crashes", "sum"),
        borough=("borough", "first")
    )

    z["filings_per_month"] = z["housing_filings"] / months
    z["sirta_per_month"] = z["sirta_crashes"] / months

    x = z["filings_per_month"].to_numpy(dtype=float)
    y = z["sirta_per_month"].to_numpy(dtype=float)

    if len(z) < 2 or np.unique(x).size < 2:
        raise ValueError("Not enough different ZIP filing values for regression.")

    slope, intercept = np.polyfit(x, y, 1)
    z["predicted_sirta"] = slope * x + intercept
    z["residual"] = z["sirta_per_month"] - z["predicted_sirta"]

    z["category"] = "Other ZIP codes"
    z.loc[z.nlargest(5, "residual").index, "category"] = "Higher than estimated"
    z.loc[z.nsmallest(5, "residual").index, "category"] = "Lower than estimated"

    fig = px.scatter(
        z,
        x="filings_per_month",
        y="sirta_per_month",
        color="category",
        color_discrete_map={
            "Other ZIP codes": "#5774E8",
            "Higher than estimated": "#1BBF9D",
            "Lower than estimated": "#F27462"
        },
        hover_name="zip",
        hover_data=[
            "borough", "housing_filings", "sirta_crashes",
            "predicted_sirta", "residual"
        ],
        title="Q6: Housing Activity and Serious Crashes by ZIP",
        labels={
            "filings_per_month": "Average monthly housing filings",
            "sirta_per_month": "Average monthly SIRTA crashes",
            "category": "Residual group"
        },
        height=600
    )

    line_x = np.linspace(x.min(), x.max(), 100)
    fig.add_scatter(
        x=line_x,
        y=slope * line_x + intercept,
        mode="lines",
        name="Linear regression",
        line=dict(color="black", dash="dash")
    )
    return fig
