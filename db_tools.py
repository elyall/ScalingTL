import sqlalchemy as db
import pandas as pd
# pull S3 models
from metaflow import Metaflow, Flow
# pull S3 datasets
import boto3
import os
from datetime import datetime


BUCKET = "metaflow-metaflows3bucket-g7dlyokq680q"
DATA_PATH = "data/"


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

def append_row(data, table):
    # data is DataFrame or dict
    if type(data) is dict:
        data = pd.DataFrame(data)
    data.to_sql(table, con=engine, if_exists="append", index=False)

def delete_row(row, table):
    # row can be dict or DataFrame with single row
    df = read_table(table)
    tbl = db.Table(table, metadata, autoload=True, autoload_with=engine)
    cond = db.and_(tbl.c['flow'] == row['flow'], tbl.c['run'] == row['run'])
    delete = tbl.delete().where(cond)
    with engine.connect() as conn:
        status = conn.execute(delete)
    return(status)

def list_flows(names="all"):
    columns = ["flow", "run", "start", "finish"]
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

def list_s3_datasets(s3_path="data/", bucket=BUCKET):
    columns= ["name", "size", "modified"]
    s3 = boto3.client('s3')
    objs = s3.list_objects_v2(Bucket=bucket, Prefix=s3_path)
    df = pd.DataFrame(columns=columns)
    for obj in objs['Contents']:
        df = df.append({
            'name': os.path.basename(obj['Key']),
            'size': obj['Size'],
            'modified': obj['LastModified']
        }, ignore_index=True)
    df['size'] = pd.to_numeric(df['size'])
    df['modified'] = pd.to_datetime(df['modified'])
    return(df)

def reset_models_table(table="models"):
    df = list_flows()
    create_table(table, 
        columns= df.columns.tolist(), 
        dtypes= db.types.String(32))
    append_row(df, table=table)

def reset_training_table(table="training"):
    create_table(table, 
        columns= ["flow", "run", "start"],
        dtypes= db.types.String(32))

def reset_data_table(table="data"):
    df = list_s3_datasets()
    create_table(table, 
        columns= df.columns.tolist(), 
        dtypes= [db.types.String(32), db.types.INTEGER(), db.types.DATETIME()])
    append_row(df, table=table)