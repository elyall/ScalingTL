from metaflow import FlowSpec, step, IncludeFile, Parameter, conda, conda_base, batch, retry, current
from datetime import datetime
from mysql.db_tools import append_row, delete_row

from io import StringIO

from os import listdir
from os.path import isfile, join

SAVE_PATH = './output/'

@conda_base(libraries={'sqlalchemy':'1.3.13','pymysql':'0.9.3','pandas':'0.23.4'}, python='3.6.8')
class TrainUniRep(FlowSpec):
    data_file = IncludeFile(
        'data_file',
        is_text=True,
        help='Input data',
        default='/home/ubuntu/input/bdata.20130222.mhci.csv')
    batch_size = Parameter('batch_size',
                        help='Batch size',
                        default=256)
    full_model = Parameter('full_model',
                        help='Use full model',
                        default=False)
    end_to_end = Parameter('end_to_end',
                        help='Train end to end',
                        default=False
    learning_rate = Parameter('learning_rate',
                        help='Learning rate',
                        default=0.001)

    @conda(libraries={'numpy':'1.15.4','tensorflow':'1.3'})
    @step
    def start(self):
        import pandas as pd
        import models.unirep_tools as ut

        # append to training registry
        self.begin = datetime.now()
        self.row = [current.flow_name, current.run_id, self.begin]
        append_row(self.row, columns=["flow", "run", "start"], table="training")
        print(current)

        # Load data
        data = StringIO(self.data_file)
        df = pd.read_csv(data)
        seqs = df.iloc[:,0].values
        vals = df.iloc[:,1].values

        # Train model
        save_path = ut.fit(seqs, vals, 
                        batch_size=self.batch_size, 
                        full_model=self.full_model, 
                        end_to_end=self.end_to_end,
                        learning_rate=self.learning_rate
                        save_path=SAVE_PATH)
        
        # Copy outputs to S3
        saved_files = [f for f in listdir(save_path) if isfile(join(save_path, f))]
        file_paths = [join(save_path, f) for f in saved_files]
        put_files = tuple(zip(saved_files, file_paths))
        with S3(s3root='s3://dataidealist/models/'+current.pathspec+'/') as s3:
            s3.put_files(put_files)

        self.next(self.end)

    @step
    def end(self):
        delete_row(self.row, table="training") # delete from training registry
        self.row.append(datetime.now())
        append_row(self.row,  columns=["flow", "run", "start", "finish"], table="metaflow") # append to trained registry
        print('TrainUniRep has finished.')


if __name__ == '__main__':
    TrainUniRep()
