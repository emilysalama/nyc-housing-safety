"""One shared look for every chart. app.py applies style_fig to each figure,
so teammates' charts match automatically and need no styling code of their own."""
BLUE, ORANGE, INK, GRID = "#0039A6", "#E8590C", "#1B2733", "#E3E8EE"
COLORWAY = [BLUE, ORANGE, "#2A9D8F", "#7B61A8", "#8D99A6"]
DIVERGING = [[0, ORANGE], [0.5, "#F7F9FB"], [1, BLUE]]  # negative = orange, positive = blue

def style_fig(fig):
    fig.update_layout(
        font=dict(family="Public Sans, Helvetica Neue, Arial, sans-serif", size=13, color=INK),
        paper_bgcolor="white", plot_bgcolor="white", colorway=COLORWAY,
        margin=dict(l=60, r=30, t=60, b=70), title=dict(font=dict(size=16), x=0.01),
        hoverlabel=dict(bgcolor="white", bordercolor=GRID, font_size=13),
        legend=dict(orientation="h", y=-0.25, x=0))
    fig.update_xaxes(gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    fig.update_coloraxes(colorscale=DIVERGING)
    return fig  