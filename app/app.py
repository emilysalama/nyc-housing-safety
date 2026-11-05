"""Dash entry point. Run from repo root: python -m app.app  (gunicorn app.app:server)"""
from pathlib import Path
import pandas as pd
from dash import Dash, html, dcc, Input, Output, State

from src.filters import filter_df, ALL
from src.dummy_data import BOROUGHS, H_COLS, T_COLS
from src.charts import q07, q08

# Real data if present, otherwise dummy data (so the app always starts).
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "clean"
if not (DATA_DIR / "zip_year_integrated.csv").exists():
    DATA_DIR = ROOT / "data" / "dummy"
ZIP_YEAR = pd.read_csv(DATA_DIR / "zip_year_integrated.csv", dtype={"zip": str})
BOROUGH_MONTH = pd.read_csv(DATA_DIR / "borough_month_integrated.csv")

# Chart registry: teammates add a line here. fn gets (filtered_df, housing_col, transport_col).
# Each entry: (graph id, tab title, table, function)
CHARTS = [
    ("q07", "Q7 Stability by year", "zip_year",
     lambda df, h, t: q07.make_fig(df, h, t)),
    ("q08", "Q8 Street-facing filings", "zip_year",
     lambda df, h, t: q08.make_fig(df, t)),
]
TABLES = {"zip_year": ZIP_YEAR, "borough_month": BOROUGH_MONTH}

def options(values):
    return [{"label": v, "value": v} for v in values]

app = Dash(__name__)
server = app.server  # gunicorn looks for this

app.layout = html.Div([
    html.H1("NYC Housing and Safety"),
    html.Div([
        dcc.Input(id="search", placeholder="Search, e.g. Brooklyn 2022 new buildings", style={"width": "320px"}),
        dcc.Dropdown(id="borough", options=options([ALL] + BOROUGHS), value=ALL, clearable=False, placeholder="Borough"),
        dcc.Dropdown(id="year", options=options([ALL, 2022, 2023, 2024, 2025]), value=ALL, clearable=False, placeholder="Year"),
        dcc.Dropdown(id="h_metric", options=options(H_COLS), value="h_new_building", clearable=False),
        dcc.Dropdown(id="t_metric", options=options(T_COLS), value="t_crashes_street", clearable=False),
        html.Button("Generate Report", id="generate", n_clicks=0),
    ], style={"display": "grid", "gridTemplateColumns": "repeat(6, 1fr)", "gap": "8px", "alignItems": "center"}),
    html.Hr(),
    *[html.Div([html.H3(title), dcc.Graph(id=cid)]) for cid, title, _, _ in CHARTS],
    html.Div(id="story"),  # M6's story section goes here
])

@app.callback(
    [Output(cid, "figure") for cid, *_ in CHARTS],
    Input("generate", "n_clicks"),
    State("borough", "value"), State("year", "value"),
    State("h_metric", "value"), State("t_metric", "value"),
)
def generate_report(_, borough, year, h_metric, t_metric):
    """Single trigger: every chart updates only when Generate Report is clicked."""
    figs = []
    for _cid, _title, table, fn in CHARTS:
        df = filter_df(TABLES[table], borough, year)
        figs.append(fn(df, h_metric, t_metric))
    return figs

if __name__ == "__main__":
    app.run(debug=True)
