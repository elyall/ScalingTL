import sqlalchemy as db
import pandas as pd
from metaflow import Metaflow, Flow

TABLE_NAME = "metaflow"
COLUMN_NAMES = ["flow", "run", "start", "finish"]
COLUMN_DTYPES = db.types.String(32)

# TABLE_NAME = "training"
# COLUMN_NAMES = ["flow", "run", "start"]
# COLUMN_DTYPES = db.types.String(32)


engine = db.create_engine('mysql+pymysql://db_user:uNw5^Hze6K&v24Z!PeCak*^n@ec2-52-38-203-135.us-west-2.compute.amazonaws.com/metaflow')
metadata = db.MetaData()

def create_table(table=TABLE_NAME, columns=COLUMN_NAMES, dtype=COLUMN_DTYPES, if_exists="replace"):
    df = pd.DataFrame(columns=columns)
    df.to_sql(table, con=engine, if_exists=if_exists, dtype=dtype, index=False)

def delete_table(table=TABLE_NAME):
    tbl = db.Table(table, metadata)
    tbl.drop(engine) #deletes the table

def read_table(table=TABLE_NAME):
    return(pd.read_sql(table, con=engine))

def append_row(data, columns=COLUMN_NAMES, table=TABLE_NAME):
    if type(data) is list: 
        data = [data] if type(data[0]) is not list else data
        data = pd.DataFrame(data, columns=columns)
    data.to_sql(table, con=engine, if_exists="append", index=False)

def delete_row(row, table=TABLE_NAME):
    # row can be dict or DataFrame with single row
    df = read_table(table)
    tbl = db.Table(table, metadata, autoload=True, autoload_with=engine)
    cond = db.and_(tbl.c['flow'] == row['flow'], tbl.c['run'] == row['run'])
    delete = tbl.delete().where(cond)
    with engine.connect() as conn:
        status = conn.execute(delete)
    return(status)

def add_s3_flows(names="all", table=TABLE_NAME):
    if isinstance(names,str) and names=="all": 
        names = []
        flows = Metaflow().flows
        for flow in flows:
            names.append(flow.pathspec)
    df = pd.DataFrame(columns=COLUMN_NAMES)
    for name in names:
        runs = list(Flow(name))
        for run in runs:
            index = run.path_components[1]
            start = run.created_at
            finish = run.finished_at
            df = df.append(dict(zip(COLUMN_NAMES, [name, index, start, finish])), ignore_index=True)
    df = df.sort_values(by=COLUMN_NAMES[:2])
    append_row(df, table=table)

def reset_models_table(columns=COLUMN_NAMES, dtype=COLUMN_DTYPES):
    create_table(TABLE_NAME, columns=columns, dtype=dtype)
    add_s3_flows(names="all", table=TABLE_NAME)

def reset_training_table():
    return(create_table("training", ["flow", "run", "start"], db.types.String(32)))