# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div(children=[
    html.H1(children='Train UniRep'),

    html.Div(children='''
        ScalingTL: a scalable, reproducible environment for performing transfer learning with UniRep.
    '''),

])

if __name__ == '__main__':
    app.run_server(host='0.0.0.0',debug=True)