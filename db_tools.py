import sqlalchemy as db
import pandas as pd
# pull S3 models
from metaflow import Metaflow, Flow
import json
# pull S3 datasets
import boto3
import os
from datetime import datetime


BUCKET = "metaflow-metaflows3bucket-g7dlyokq680q"
DATA_PATH = "data/"
MODEL_PATH = "models/"

# Create connection path
create_path = 'mysql+pymysql://db_user:uNw5^Hze6K&v24Z!PeCak*^n@'
import sys
if sys.platform == "linux" or sys.platform == "linux2":
    create_path = create_path + '10.20.0.5'
elif sys.platform == "darwin":
    create_path = create_path + 'ec2-44-230-85-65.us-west-2.compute.amazonaws.com'
create_path = create_path + '/metaflow'

# Create connection objects
engine = db.create_engine(create_path)
metadata = db.MetaData()


def create_table(table, columns, dtypes, if_exists="replace"):
    df = pd.DataFrame(columns=columns)
    if isinstance(dtypes, list): dtypes = dict(zip(columns, dtypes))
    df.to_sql(table, con=engine, if_exists=if_exists, dtype=dtypes, index=False)

def delete_table(table):
    tbl = db.Table(table, metadata)
    tbl.drop(engine) #deletes the table

def read_table(table):
    return(pd.read_sql(table, con=engine))

def write_row(data, table, if_exists="append"):
    # data is DataFrame or dict
    if type(data) is dict:
        try:
            data = pd.DataFrame(data)
        except ValueError:
            data = pd.DataFrame([data])
    data.to_sql(table, con=engine, if_exists=if_exists, index=False)

def delete_row(row, table):
    # row can be dict or DataFrame with single row
    df = read_table(table)
    tbl = db.Table(table, metadata, autoload=True, autoload_with=engine)
    cond = db.and_(tbl.c['flow'] == row['flow'], tbl.c['id'] == row['id'])
    delete = tbl.delete().where(cond)
    with engine.connect() as conn:
        status = conn.execute(delete)
    return(status)

def list_flows(names="all"):
    columns = ["flow", "id", "start", "finish"]
    if isinstance(names,str) and names=="all": 
        names = []
        flows = Metaflow().flows
        for flow in flows:
            names.append(flow.pathspec)
    df = pd.DataFrame(columns= columns)
    for name in names:
        runs = list(Flow(name))
        for run in runs:
            index = run.path_components[1]
            start = run.created_at
            finish = run.finished_at
            df = df.append(dict(zip(columns, [name, index, start, finish])), ignore_index=True)
    return(df.sort_values(by=columns[:2]))

def list_s3_models(s3_path=MODEL_PATH, bucket=BUCKET):
    s3_client = boto3.client('s3')
    objs = s3_client.list_objects_v2(Bucket=bucket, Prefix=s3_path)
    columns = ["flow", "id", "size", "features", "mse", "finish"]
    df = pd.DataFrame(columns=columns)
    if objs['KeyCount']:
        for obj in objs['Contents']:
            if obj['Key'].endswith('.json'):
                fileObj = s3_client.get_object(Bucket=bucket, Key=obj['Key'])
                file_content = fileObj['Body'].read().decode('utf-8')
                data = json.loads(file_content)
                data = {k:data[k] for k in columns if k in data}
                df = df.append(data, ignore_index=True)
    df['mse'] = pd.to_numeric(df['mse'])
    df['finish'] = pd.to_datetime(df['finish'])
    return(df.sort_values(by=['flow', 'finish', 'id']))

def get_s3_data_features(s3_path, bucket=BUCKET, num_bytes=1000, s3_client=None):
    if s3_client is None: s3_client = boto3.client('s3')
    fileObj = s3_client.get_object(Bucket=bucket, Key=s3_path)
    header = fileObj['Body'].read(num_bytes).decode('utf-8') # read small part of file
    columns = header.split('\n')[0] # grab first row -> column names
    features = columns[columns.find(',')+1:] # ignore first column which is sequence
    return(features)

def list_s3_datasets(s3_path=DATA_PATH, bucket=BUCKET):
    columns= ["name", "features", "size", "modified"]
    s3_client = boto3.client('s3')
    objs = s3_client.list_objects_v2(Bucket=bucket, Prefix=s3_path)
    df = pd.DataFrame(columns=columns)
    for obj in objs['Contents']:
        features = get_s3_data_features(obj['Key'], bucket=bucket, s3_client=s3_client)
        df = df.append({
            'name': os.path.basename(obj['Key']),
            'features': features,
            'size': obj['Size'],
            'modified': obj['LastModified']
        }, ignore_index=True)
    df['size'] = pd.to_numeric(df['size'])
    df['modified'] = pd.to_datetime(df['modified'])
    return(df)

def reset_models_table(table="models"):
    df = list_s3_models()
    # create_table(table, 
    #     columns= df.columns.tolist(), 
    #     dtypes= db.types.String(64))
    write_row(df, table=table, if_exists='replace')

def reset_training_table(table="training"):
    create_table(table, 
        columns= ["flow", "id", "data_file", "features", "size", "start"],
        dtypes= db.types.String(64))

def reset_data_table(table="data"):
    df = list_s3_datasets()
    # create_table(table, 
    #     columns= df.columns.tolist(), 
    #     dtypes= [db.types.String(64), db.types.String(128), db.types.INTEGER(), db.types.DATETIME()])
    write_row(df, table=table, if_exists='replace')