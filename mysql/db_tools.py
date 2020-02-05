import sqlalchemy as db
import pandas as pd
from metaflow import Metaflow, Flow

TABLE_NAME = "metaflow"
COLUMNS = ["flow", "run", "start", "finish"]
DTYPE = db.types.String(32)

engine = db.create_engine('mysql+pymysql://db_user:uNw5^Hze6K&v24Z!PeCak*^n@ec2-52-38-203-135.us-west-2.compute.amazonaws.com/metaflow')
metadata = db.MetaData()
connection = engine.connect()

def create_table(table_name=TABLE_NAME, columns=COLUMNS, dtype=DTYPE, if_exists="replace"):
    df = pd.DataFrame(columns=columns)
    df.to_sql(table_name, con=engine, if_exists=if_exists, dtype=dtype, index=False)

def delete_table(table_name=TABLE_NAME):
    tbl = db.Table(table_name, metadata)
    tbl.drop(engine) #deletes the table

def append_flow(data, columns=COLUMNS, table_name=TABLE_NAME):
    if isinstance(data, list): data = pd.DataFrame(data, columns=columns)
    data.to_sql(table_name, con=engine, if_exists="append", index=False)

def pull_from_s3(names="all", table_name=TABLE_NAME):
    if isinstance(names,str) and names=="all": 
        names = []
        flows = Metaflow().flows
        for flow in flows:
            names.append(flow.pathspec)
    df = pd.DataFrame(columns=COLUMNS)
    for name in names:
        runs = list(Flow(name))
        for run in runs:
            index = run.path_components[1]
            start = run.created_at
            finish = run.finished_at
            df = df.append(dict(zip(COLUMNS, [name, index, start, finish])), ignore_index=True)
    df = df.sort_values(by=COLUMNS[:2])
    append_flow(df, table_name=table_name)

def reset_table(table_name=TABLE_NAME, columns=COLUMNS, dtype=DTYPE):
    create_table(table_name=table_name, columns=columns, dtype=dtype)
    pull_from_s3(names="all", table_name=table_name)

def read_table(table_name=TABLE_NAME):
    df = pd.read_sql(table_name, con=engine)
    return(df)