import sqlalchemy as db
import pandas as pd

engine = db.create_engine('mysql+pymysql://db_user:uNw5^Hze6K&v24Z!PeCak*^n@ec2-52-38-203-135.us-west-2.compute.amazonaws.com/metaflow.db')
# engine = sql.create_engine('postgres+psycopg2://db_user:uNw5^Hze6K&v24Z!PeCak*^n@ec2-52-38-203-135.us-west-2.compute.amazonaws.com')

def init_table():
    connection = engine.connect()
    metadata = db.MetaData()
    tbl = db.Table('metaflow', metadata,
                db.Column('flow', db.types.String(32), nullable=False),
                db.Column('index', db.types.Integer(), nullable=False),
                db.Column('start', db.types.DateTime(), nullable=True),
                db.Column('finish', db.types.DateTime(), nullable=True)
                )
    metadata.create_all(engine) #creates the table

def append_flow(flow, index, start, finish):
    connection = engine.connect()
    metadata = db.MetaData()
    tbl = db.Table('metaflow', metadata, autoload=True, autoload_with=engine)
    query = db.insert(tbl).values(flow=flow, index=index, start=time, finish=time) 
    return(connection.execute(query))

def read_table():
    connection = engine.connect()
    metadata = db.MetaData()
    tbl = db.Table('metaflow', metadata, autoload=True, autoload_with=engine)
    results = connection.execute(db.select([tbl])).fetchall()
    return(pd.DataFrame(results))