# -*- coding: utf-8 -*-

# append ScalingTL & UniRep to path
import sys
if sys.platform == "linux" or sys.platform == "linux2":
    MODULE_PATH = '/home/ubuntu/ScalingTL/'
elif sys.platform == "darwin":
    MODULE_PATH = '/Users/elyall/Dropbox/Projects/Insight/ScalingTL/'
sys.path.append(MODULE_PATH)

# website
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html

# loading data
from dash_table import DataTable
import base64
import datetime
import io
import pandas as pd
import os

# running metaflow
import subprocess

# loading model registries
from db_tools import read_table
from data_IO import download_obj_from_s3

PAGE_SIZE = 20
LOCAL_PATH = "tmp/"

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

if not os.path.exists(LOCAL_PATH):
    os.makedirs(LOCAL_PATH) # create directory for objects pulled from S3
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
    html.Div(id='hidden-div', children=None, style={'display':'none'}),
    dcc.Tabs([
        dcc.Tab(label="Train", children=[
            html.H3(children='Select Data'),

            dcc.Dropdown(
                id='select-data',
                options=[
                    {'label': 'Select a preloaded dataset', 'value': 'none'},
                    {'label': 'MHC1', 'value': 'mhc1'},
                ],
                value='none'
            ),
            
            # html.H6(children='OR'),
            # html.Div(children='''
            #     Train on your own data: load a .csv file where the first column is amino acid sequences and any additional column is a measured feature
            # '''),
            # dcc.Upload(
            #     id='upload-data',
            #     children=html.Div([
            #         'Drag and Drop or ',
            #         html.A('Select Files')
            #     ]),
            #     style={
            #         'width': '100%',
            #         'height': '60px',
            #         'lineHeight': '60px',
            #         'borderWidth': '1px',
            #         'borderStyle': 'dashed',
            #         'borderRadius': '5px',
            #         'textAlign': 'center',
            #         'margin': '10px'
            #     },
            #     multiple=False
            # ),
            html.Div(id='output-data-select'),
            # html.Div(id='output-data-upload'),

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


# @app.callback(Output('output-data-upload', 'children'),
#               [Input('upload-data', 'contents')],
#               [State('upload-data', 'filename'),
#                State('upload-data', 'last_modified')])
# def update_output(contents, filename, date):
#     if contents is not None:
#         content_type, content_string = contents.split(',')
#         decoded = base64.b64decode(content_string)
#         ext = filename.split('.')[-1]
#         try:
#             if ext=='csv':
#                 data_file = io.StringIO(decoded.decode('utf-8'))
#                 df = pd.read_csv(data_file)
#             elif ext=='xls':
#                 data_file = io.BytesIO(decoded)
#                 df = pd.read_excel(data_file)
#         except Exception as e:
#             print(e)
#             return html.Div([
#                 'There was an error processing this file.'
#             ])
#         df.to_csv(TMP)
#         return html.Div([
#             html.H5(filename),
#             html.H6(datetime.datetime.fromtimestamp(date)),

#             DataTable(
#                 data=df.to_dict('records'),
#                 columns=[{'name': i, 'id': i} for i in df.columns],
#                 page_size=PAGE_SIZE
#             ),

#         ])

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
                        "--environment=conda", 
                        "run",
                        "--s3_file", s3_path],
                        stdout= logfile,
                        stderr= subprocess.STDOUT)
    return(0)

if __name__ == '__main__':
    app.run_server(host='0.0.0.0',debug=True)