from dash import Dash, html

app = Dash(__name__)
server = app.server  # gunicorn looks for this

app.layout = html.Div([html.H1("NYC Housing and Safety: hello")])

if __name__ == "__main__":
    app.run(debug=True)
