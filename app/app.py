"""Dash entry point. Run from repo root: python -m app.app  (gunicorn app.app:server)"""
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output, State

from src.filters import filter_df, ALL
from src.dummy_data import BOROUGHS, H_COLS, T_COLS
from src.charts import q07, q08
from src.theme import style_fig

ROOT = Path(__file__).resolve().parent.parent

def load(name, **kw):
    """Load data/clean/<name>, else data/dummy/<name>, else None (so the app always starts)."""
    for folder in ("clean", "dummy"):
        path = ROOT / "data" / folder / name
        if path.exists():
            return pd.read_csv(path, **kw)
    return None

# M3's confirmed tables, plus the extra tables Q2/Q11 need (None until the files exist).
TABLES = {
    "zip_year": load("zip_year_integrated.csv", dtype={"zip": str}),
    "borough_month": load("borough_month_integrated.csv"),
    "crashes": load("crash_clean.csv", dtype={"zip": str}),
    "sites": load("housing_sites_points.csv", dtype={"zip": str}),
}

# Chart registry. Teammates add one entry.
#   fn(tables, housing_col, transport_col) -> figure; tables is a dict (filtered or not, see 'filtered')
#   needs: table names that must exist, otherwise the chart shows a message
#   filtered: False for charts that ignore Borough/Year (e.g. Q12), a note appears under them
CHARTS = [
    dict(id="q07", title="Q7 Stability by year", needs=["zip_year"], filtered=True,
         fn=lambda T, h, t: q07.make_fig(T["zip_year"], h, t),
         hint="Each cell compares ZIP codes within one borough and year. Blue means ZIPs with more filings also had more crashes; orange means the opposite."),
    dict(id="q08", title="Q8 Street-facing filings", needs=["zip_year"], filtered=True,
         fn=lambda T, h, t: q08.make_fig(T["zip_year"], t),
         hint="Taller bars mean that filing type moves more closely with serious crashes across ZIP codes."),
    # Q11 example (exception to make_fig(df)):
    # dict(id="q11", title="Q11 ...", needs=["crashes", "zip_year"], filtered=True,
    #      fn=lambda T, h, t: q11.make_fig(q11.prepare(T["crashes"], T["zip_year"])), hint="..."),
    # Q12 example (ignores filters, needs scikit-learn):
    # dict(id="q12", title="Q12 ...", needs=["zip_year"], filtered=False,
    #      fn=lambda T, h, t: q12.make_fig(T["zip_year"]), hint="..."),
]

def options(values):
    return [{"label": v, "value": v} for v in values]

def message_fig(text):
    fig = go.Figure()
    fig.add_annotation(text=text, showarrow=False, font=dict(size=14))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig

app = Dash(__name__)
server = app.server  # gunicorn looks for this

def field(label, component):
    return [html.Label(label), component]

def chart_card(c):
    note = "" if c["filtered"] else " This chart ignores the Borough and Year filters."
    return html.Div([html.H3(c["title"]), html.P(c["hint"] + note, className="hint"),
                     dcc.Loading(dcc.Graph(id=c["id"], config={"displaylogo": False}), type="dot", color="#0039A6")],
                    className="card")

app.layout = html.Div([
    html.Div([html.H1("NYC Housing and Street Safety"),
              html.P("Does new construction show up alongside serious crashes? Pick filters, then generate the report.")],
             className="topbar"),
    html.Div([
        html.Div([
            *field("Search", dcc.Input(id="search", placeholder="Brooklyn 2022 new buildings")),
            *field("Borough", dcc.Dropdown(id="borough", options=options([ALL] + BOROUGHS), value=ALL, clearable=False)),
            *field("Year", dcc.Dropdown(id="year", options=options([ALL, 2022, 2023, 2024, 2025]), value=ALL, clearable=False)),
            *field("Housing measure", dcc.Dropdown(id="h_metric", options=options(H_COLS), value="h_new_building", clearable=False)),
            *field("Crash measure", dcc.Dropdown(id="t_metric", options=options(T_COLS), value="t_crashes_street", clearable=False)),
            html.Button("Generate Report", id="generate", n_clicks=0, className="btn btn-primary"),
            html.Button("Reset filters", id="reset", n_clicks=0, className="btn btn-ghost"),
        ], className="panel"),
        html.Div([
            html.Div(id="summary", className="summary"),
            *[chart_card(c) for c in CHARTS],
            html.Div(id="story"),  # M6's story section goes here
        ]),
    ], className="layout"),
])

@app.callback(
    [Output(c["id"], "figure") for c in CHARTS] + [Output("summary", "children")],
    Input("generate", "n_clicks"),
    State("borough", "value"), State("year", "value"),
    State("h_metric", "value"), State("t_metric", "value"),
)
def generate_report(_, borough, year, h_metric, t_metric):
    """Single trigger: every chart updates only when Generate Report is clicked."""
    filtered = {name: filter_df(df, borough, year) for name, df in TABLES.items() if df is not None}
    unfiltered = {name: df for name, df in TABLES.items() if df is not None}
    figs = []
    for c in CHARTS:
        missing = [n for n in c["needs"] if n not in unfiltered]
        if missing:
            figs.append(message_fig(f"Waiting for data: {', '.join(missing)}"))
            continue
        try:
            fig = c["fn"](filtered if c["filtered"] else unfiltered, h_metric, t_metric)
            figs.append(style_fig(fig))
        except Exception as e:  # one broken chart must not break the others
            figs.append(message_fig(f"{c['title']} failed: {e}"))
    summary = f"Showing {borough if borough != ALL else 'all boroughs'}, {year if year != ALL else '2022 to 2025'}. Housing: {h_metric}. Crashes: {t_metric}."
    return figs + [summary]

@app.callback(Output("borough", "value"), Output("year", "value"), Output("h_metric", "value"),
              Output("t_metric", "value"), Output("search", "value"), Input("reset", "n_clicks"),
              prevent_initial_call=True)
def reset_filters(_):
    return ALL, ALL, "h_new_building", "t_crashes_street", ""

if __name__ == "__main__":
    app.run(debug=True)