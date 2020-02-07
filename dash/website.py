# -*- coding: utf-8 -*-
# append ScalingTL & UniRep to path
import sys, os
sys.path.append(os.path.join('home','ubuntu','ScalingTL'))
sys.path.append(os.path.join('home','ubuntu','ScalingTL','models','UniRep'))

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html

# loading own data
from dash_table import DataTable
import base64
import datetime
import io
import pandas as pd

# running metaflow
import subprocess

# loading model registries
from mysql.db_tools import read_table

PAGE_SIZE = 20

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
df_trained = read_table("metaflow")
df_running = read_table("training")


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title = "ScalingTL"

app.layout = html.Div(children=[
    html.H1(children='ScalingTL'),
    html.H6(children='''
        A scalable, version controlled transfer learning pipeline for UniRep.
    '''),
    html.Div(id='hidden-div', style={'display':'none'}),
    dcc.Tabs([
        dcc.Tab(label="Train", children=[
            html.H3(children='Select Data'),

            html.Div(children='Select a preloaded dataset'),
            dcc.Dropdown(
                options=[
                    {'label': 'MHCI', 'value': 'mhc1'},
                    {'label': 'PLACEHOLDER', 'value': 'tbd'},
                ],
                value='mhc1'
            ),
            
            html.H6(children='OR'),
            html.Div(children='''
                Train on your own data: load a .csv file where the first column is amino acid sequences and any additional column is a measured feature
            '''),
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px'
                },
                # Allow multiple files to be uploaded
                multiple=True
            ),
            html.Div(id='output-data-upload'),

            html.Hr(),
            html.Button(
                ['Train'],
                id='btn_train'
            ),
            html.Hr(),

            html.H3(children='Training models:'),

            DataTable(
                id='table_training',
                data=df_running.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df_running.columns],
                page_size=PAGE_SIZE,
                page_current=0
            ),

            html.Button(
                ['Update'],
                id='btn_training'
            )
        ]),

        dcc.Tab(label="Inference", children=[
            html.H3(children='Trained models:'),

            DataTable(
                id='table_models',
                data=df_trained.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df_trained.columns],
                page_size=PAGE_SIZE,
                page_current=0
            ),

            html.Button(
                ['Update'],
                id='btn_models'
            )
        ])
    ])
])

def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    ext = filename.split('.')[-1]
    try:
        if ext=='csv':
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif ext=='xls':
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),

        DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns],
            page_size=PAGE_SIZE
        ),

    ])

@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children

@app.callback(Output('table_training', 'data'),
    [Input('btn_training', 'n_clicks')])
def update_training(n_clicks):
    if n_clicks:
        df = read_table('training')
    else:
        df = df_running
    return(df.to_dict('records'))
    
@app.callback(Output('table_models', 'data'),
    [Input('btn_models', 'n_clicks')])
def update_models(n_clicks):
    if n_clicks:
        df = read_table('metaflow')
    else:
        df = df_trained
    return(df.to_dict('records'))

@app.callback(Output('hidden-div', 'n_clicks'),
    [Input('btn_train', 'n_clicks')])
def train_model(n_clicks):
    if n_clicks:
        subprocess.Popen(["python3","/home/ubuntu/ScalingTL/metaflow/TrainUniRep.py","--environment=conda","run"])
        print('started flow')
    return(0)

if __name__ == '__main__':
    app.run_server(host='0.0.0.0',debug=True)