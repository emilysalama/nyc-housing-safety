"""Q8: Do street-facing filings (sidewalk sheds, curb cuts) track serious crashes
better than other alterations? Table: zip_year. Chart: grouped bars of Spearman rho."""
import pandas as pd
import plotly.express as px
from src.charts.q07 import spearman

METRICS = {"h_sidewalk_shed": "Sidewalk sheds", "h_curb_cut": "Curb cuts",
           "h_alteration_co": "Alteration CO (other alterations)"}

def make_fig(df, transport_col="t_crashes_street"):
    rows = []
    groups = [("All boroughs", df)] + list(df.groupby("borough"))
    for name, g in groups:
        if len(g) < 5:
            continue
        for col, label in METRICS.items():
            rows.append({"borough": name, "metric": label, "rho": spearman(g[col], g[transport_col])})
    res = pd.DataFrame(rows)
    if res.empty:
        return px.bar(title="No data for the selected filters")
    fig = px.bar(res, x="borough", y="rho", color="metric", barmode="group",
                 range_y=[-1, 1], labels=dict(rho="Spearman rho", borough="Borough", metric="Filing type"),
                 title=f"Correlation with {transport_col} (ZIP-year level)")
    fig.add_hline(y=0, line_width=1)
    return fig
