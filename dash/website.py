# -*- coding: utf-8 -*-

# append ScalingTL to path
import sys
if sys.platform == "linux" or sys.platform == "linux2":
    MODULE_PATH = '/home/ubuntu/ScalingTL/'
elif sys.platform == "darwin":
    MODULE_PATH = '/Users/elyall/Dropbox/Projects/Insight/ScalingTL/'
sys.path.append(MODULE_PATH)
# loading registries
from db_tools import read_table, append_row
from data_IO import download_obj_from_s3, upload_files_to_s3

# website
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from dash_table import DataTable
import pandas as pd

# running metaflow
import subprocess

# loading data for display
import base64
import io
import os

PAGE_SIZE = 20
LOCAL_PATH = "tmp/"
BUCKET = "metaflow-metaflows3bucket-g7dlyokq680q"

if not os.path.exists(LOCAL_PATH):
    os.makedirs(LOCAL_PATH) # create directory for objects pulled from S3
df_trained = read_table("metaflow")
df_running = read_table("training")
df_datasets = read_table("datasets")


# Create website
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title = "ScalingTL"

app.layout = html.Div(children=[
    html.H1(children='ScalingTL'),
    html.H6(children='''
        A scalable, version controlled transfer learning pipeline for UniRep.
    '''),

    html.Hr(),
    html.H3(children='Select a Starting Model'),
    DataTable(
        id='table_models',
        data=df_trained.to_dict('records'),
        columns=[{"name": i, "id": i} for i in df_trained.columns],
        page_size=PAGE_SIZE,
        page_current=0,
        row_selectable='single'
    ),
    html.Button(
        ['Update'],
        id='btn_models'
    ),

    html.Hr(),
    html.Div(children='''
        [Optional] Upload your own data:
        Load a .csv file where the first column is amino acid sequences and any additional column is a measured feature where the feature label is the column name.
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
        multiple=False
    ),
    
    html.Hr(),
    html.H3(children='Select a Dataset'),
    DataTable(
        id='table_data',
        data=df_datasets.to_dict('records'),
        columns=[{"name": i, "id": i} for i in df_datasets.columns],
        page_size=PAGE_SIZE,
        page_current=0,
        row_selectable='single'
    ),
    html.Div(id='output-data-select'),

    html.Div(id='hidden-div', children=None, style={'display':'none'}),
    dcc.Tabs([
        dcc.Tab(label="Train", children=[

            html.Hr(),
            html.Button(
                ['Train'],
                id='btn_train',
            ),

            html.Hr(),
            html.H3(children='Training models:'),
            DataTable(
                id='table_training',
                data=df_running.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df_running.columns],
                page_size=PAGE_SIZE,
                page_current=0,
                row_selectable='single'
            ),
            html.Button(
                ['Update'],
                id='btn_training'
            )
        ]),

        dcc.Tab(label="Predict", children=[
            html.Div(children='''
                UNDER DEVELOPMENT
            '''),
        ])
    ])
])

# CALLBACK: SELECT A MODEL?

# Upload data callback
@app.callback(Output('table_data', 'data'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_output(contents, filename, date):
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        ext = filename.split('.')[-1]
        try:
            if ext=='csv':
                data_file = io.StringIO(decoded.decode('utf-8'))
                df = pd.read_csv(data_file, nrows=0)
            elif ext=='xls':
                data_file = io.BytesIO(decoded)
                df = pd.read_excel(data_file, nrows=0)
        except Exception as e:
            print(e)
            return html.Div([
                'There was an error processing this file.'
            ])
        upload_files_to_s3(data_file, s3_path='data/', bucket=BUCKET) # upload data
        df = pd.DataFrame({'name': filename, 'features': df.columns.tolist(), 'size': date, 'modified', date})
        append_row(df, table="datasets") # upload registry to database
        df_datasets = read_table("datasets")
        return(df_datasets.to_dict('records'))

@app.callback([Output('output-data-select', 'children'),
            Output('hidden-div', 'children')],
            [Input('select-data', 'value')])
def update_output2(value):
    if value=="mhc1":
        s3_path = "s3://metaflow-metaflows3bucket-g7dlyokq680q/data/bdata.20130222.mhci.csv"
        filename = download_obj_from_s3('data/bdata.20130222.mhci.csv', bucket='metaflow-metaflows3bucket-g7dlyokq680q', directory=LOCAL_PATH)
        df = pd.read_csv(filename, nrows=100)
        children = html.Div([
            html.H5(filename.split("/")[-1]),
            DataTable(
                data=df.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df.columns],
                page_size=PAGE_SIZE
            )
        ])
    else:
        children = []
        s3_path = None
    return(children, s3_path)

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
    [Input('btn_train', 'n_clicks'),
    Input('hidden-div', 'children')])
def train_model(n_clicks, s3_path):
    if n_clicks and s3_path:
        with open(LOCAL_PATH+"log.txt", "a") as logfile:
            subprocess.Popen(["python3", MODULE_PATH+"TrainUniRep.py",
                        "run",
                        "--s3_file", s3_path,
                        "--with", "batch"],
                        stdout= logfile,
                        stderr= subprocess.STDOUT)
    return(0)

if __name__ == '__main__':
    app.run_server(host='0.0.0.0')
