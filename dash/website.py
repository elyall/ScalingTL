# -*- coding: utf-8 -*-

# append ScalingTL to path
import sys
if sys.platform == "linux" or sys.platform == "linux2":
    MODULE_PATH = '/home/ubuntu/ScalingTL/'
elif sys.platform == "darwin":
    MODULE_PATH = '/Users/elyall/Dropbox/Projects/Insight/ScalingTL/'
sys.path.append(MODULE_PATH)
# loading registries
from db_tools import read_table, write_row
from data_IO import download_obj_from_s3, upload_file_to_s3

# website
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from dash_table import DataTable
import pandas as pd

# running metaflow
import subprocess

# uploading and downloading data
import base64
import io
import os
from datetime import datetime

PAGE_SIZE = 20
LOCAL_PATH = "tmp/"
BUCKET = "metaflow-metaflows3bucket-g7dlyokq680q"

if not os.path.exists(LOCAL_PATH):
    os.makedirs(LOCAL_PATH) # create directory for objects pulled from S3
df_trained = read_table("models")
df_running = read_table("training")
df_datasets = read_table("data")

click_counter = 0

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
    html.H3(children='Select a starting model'),
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
    html.Div(id='output-model-select'),
    html.Div(id='hidden-model', children=None, style={'display':'none'}),

    html.Hr(),
    html.H3(children='[Optional] Upload your own data'),
    html.Div(children='''
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
    html.H3(children='Select a dataset'),
    DataTable(
        id='table_data',
        data=df_datasets.to_dict('records'),
        columns=[{"name": i, "id": i} for i in df_datasets.columns],
        page_size=PAGE_SIZE,
        page_current=0,
        row_selectable='single'
    ),
    html.Div(id='output-data-select'),
    html.Div(id='hidden-data', children=None, style={'display':'none'}),

    # dcc.Tabs([
    #     dcc.Tab(label="Train", children=[

    html.Hr(),
    html.H3(children='Start transfer learning'),
    dcc.Dropdown(
        id='train-type',
        options=[
            {'label': 'End to end', 'value': 'true'},
            {'label': 'Top layer only', 'value': 'false'}
        ],
        value='true',
        style={'width': '280px'}
    ),
    html.Div(['Batch size: ', dcc.Input(
            id='train-batch-size',
            type='number',
            placeholder=256,
            value=256
        )]),
    html.Div(['Learning rate: ', dcc.Input(
        id='train-learning-rate',
        type='number',
        placeholder=0.001,
        value=0.001
    )]),
    html.Button(
        ['Train'],
        id='btn_train',
    ),
    html.Div(children='', id='train-error'),

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

        # ]),

        # dcc.Tab(label="Predict", children=[
        #     html.Div(children='''
        #         UNDER DEVELOPMENT
        #     '''),
        # ])
    # ])
])

@app.callback([Output('output-model-select', 'children'),
            Output('hidden-model', 'children')],
            [Input('table_models', 'data'),
            Input('table_models', 'derived_virtual_selected_rows')])
def select_model(models, selected_row):
    if selected_row:
        s3_path = 's3://' + BUCKET + '/models/' + models[selected_row[0]]['flow'] + '/' + models[selected_row[0]]['id'] + '/'
        # DISPLAY ANALYSIS OF MODEL? e.g. correlation of test data actual vs predicted for different features
        # filename = download_obj_from_s3(s3_path+'metadata.json', directory=LOCAL_PATH)
        # with open(filename) as json_file:
        #     data = json.load(json_file)
        # children = html.Div([
        #     html.H5(filename.split("/")[-1]),
        #     DataTable(
        #         data=data,
        #         columns=[{'name': i, 'id': i} for i in data],
        #         page_size=PAGE_SIZE
        #     )
        # ])
        children = []
    else:
        children = []
        s3_path = None
    return(children, s3_path)

def io_size(io_obj):
    pos = io_obj.tell()
    io_obj.seek(0, os.SEEK_END)
    size = io_obj.tell()
    io_obj.seek(pos) # reset
    return(size)

@app.callback(Output('table_data', 'data'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def upload_data(contents, filename, date):
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        ext = filename.split('.')[-1]
        try:
            if ext=='csv':
                data_file = io.StringIO(decoded.decode('utf-8'))
                df = pd.read_csv(data_file, nrows=0) # to get features
                data_file = io.BytesIO(data_file.getvalue().encode()) # convert to bytesio for uploading to S3 (needs .read() method)
            elif ext=='xls':
                data_file = io.BytesIO(decoded)
                df = pd.read_excel(data_file, nrows=0)
            features = df.columns.tolist()[1:]
            if len(features)>1: features = ','.join(features)
            else: features = features[0]
            meta = pd.DataFrame([{'name': filename, 'features': features, 'size': io_size(data_file), 'modified': datetime.fromtimestamp(date)}])
            upload_file_to_s3(data_file, key=filename, s3_path='data/', bucket=BUCKET) # upload data to s3
            write_row(meta, table='data') # upload registry to database
            df = df_datasets.append(meta, sort=False)
        except Exception as e:
            print(e)
            return html.Div([
                'There was an error processing this file.'
            ])
    else: df = df_datasets
    return(df.to_dict('records'))

@app.callback([Output('output-data-select', 'children'),
            Output('hidden-data', 'children')],
            [Input('table_data', 'data'),
            Input('table_data', 'derived_virtual_selected_rows')])
def select_dataset(datasets, selected_row):
    if selected_row:
        s3_path = 's3://' + BUCKET + '/data/' + datasets[selected_row[0]]['name']
        filename = download_obj_from_s3(s3_path, directory=LOCAL_PATH)
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

@app.callback(Output('train-error', 'children'),
    [Input('btn_train', 'n_clicks'),
    Input('hidden-data', 'children'),
    Input('hidden-model', 'children'),
    Input('train-type', 'value'),
    Input('train-batch-size', 'value'),
    Input('train-learning-rate', 'value')])
def train_model(n_clicks, s3_data_path, s3_weights_path, end_to_end, batch_size, learning_rate):
    global click_counter
    if n_clicks and n_clicks > click_counter:
        click_counter += 1
        if not s3_weights_path:
            return('Select a model!')
        if not s3_data_path:
            return('Select a dataset!')
        with open(os.path.join(LOCAL_PATH,"log.txt"), "a") as logfile:
            print('Data: ' + s3_data_path)
            print('Weights: ' + s3_weights_path)
            subprocess.Popen(["python3", os.path.join(MODULE_PATH,"TrainUniRep.py"),
                        "run",
                        "--s3_file", s3_data_path,
                        "--weights_path", s3_weights_path,
                        "--batch_size", str(batch_size),
                        "--end_to_end", end_to_end,
                        "--learning_rate", str(learning_rate),
                        "--with", "batch"],
                        stdout= logfile,
                        stderr= subprocess.STDOUT)
            return('Training ' + '/'.join(s3_weights_path.split('/')[-3:]) + ' on ' + s3_data_path.split('/')[-1])
    return('')

if __name__ == '__main__':
    app.run_server(host='0.0.0.0')
