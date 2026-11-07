"""Q10: Are ZIPs where new buildings take longer from permit to sign-off linked to more serious crashes?
Table: zip_year. Chart: scatter of median days (x) against crashes (y), sized by new-building filings."""
import plotly.express as px
import plotly.graph_objects as go

X_COL = "h_median_days_permit_to_signoff"
SIZE_COL = "h_new_building"
MIN_POINTS = 10  # a correlation on fewer ZIP-years is too noisy to report


def spearman(x, y):
    """Spearman = Pearson on ranks (same helper as Q7, no scipy needed)."""
    return x.rank().corr(y.rank())


def message_fig(text):
    fig = go.Figure()
    fig.add_annotation(text=text, showarrow=False, font=dict(size=14))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def make_fig(df, transport_col="t_crashes_street"):
    # A median exists only where at least one new building has a sign-off date. NaN is not 0, so drop it.
    data = df.dropna(subset=[X_COL])
    if data.empty:
        return message_fig("No ZIP-years with a completed new building for the selected filters")
    data = data.assign(buildings=data[SIZE_COL].clip(lower=1))  # bubble size must be positive

    rho = spearman(data[X_COL], data[transport_col]) if len(data) >= MIN_POINTS else float("nan")
    rho_text = f"Spearman rho = {rho:.2f}" if rho == rho else "too few points for a correlation"

    fig = px.scatter(
        data, x=X_COL, y=transport_col, size="buildings", size_max=28, color="borough",
        hover_name="zip", hover_data={"year": True, "buildings": ":.0f", X_COL: ":.0f"},
        opacity=0.65,
        labels={X_COL: "Median days from first permit to sign-off", transport_col: transport_col,
                "buildings": "New-building filings", "borough": "Borough"},
        title=f"Build time vs serious crashes by ZIP ({rho_text}, n = {len(data)} ZIP-years)")
    fig.add_annotation(
        xref="paper", yref="paper", x=0, y=-0.30, showarrow=False, align="left",
        text=(f"Showing {len(data)} of {len(df)} ZIP-years: only ZIPs with a signed-off new building have a median. "
              "Recent filings are less likely to be signed off yet, so later years lean toward fast projects. "
              "Association only, not causation."))
    return fig
