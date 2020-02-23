from metaflow import FlowSpec, step, IncludeFile, Parameter, current, S3
from datetime import datetime
from db_tools import write_row, delete_row

from io import StringIO

from os import listdir
from os.path import isfile, join
import json

SAVE_PATH = "output/"
BUCKET = 'metaflow-metaflows3bucket-g7dlyokq680q'
model_columns = ["flow", "id", "size", "features", "mse", "finish"]

class TrainUniRep(FlowSpec):
    local_file = IncludeFile(
        'local_file',
        is_text=True,
        help='Input data',
        default=None)
    s3_file = Parameter('s3_file',
                        help='File on S3',
                        default='s3://'+BUCKET+'/data/mhci binding affinity.csv')
    weights_path = Parameter('weights_path',
                        help='Location of weights on S3',
                        default='s3://'+BUCKET+'/models/UniRep/base64/')
    batch_size = Parameter('batch_size',
                        help='Batch size',
                        default='256')
    end_to_end = Parameter('end_to_end',
                        help='Train end to end',
                        default='true')
    learning_rate = Parameter('learning_rate',
                        help='Learning rate',
                        default='0.001')

    @step
    def start(self):
        self.begin = datetime.now()

        import pandas as pd
        import unirep_tools as ut

        # Load data
        if self.local_file:
            self.file_name = ''
            df = pd.read_csv(StringIO(self.local_file), index_col=False)
        elif self.s3_file:
            self.file_name = self.s3_file.split('/')[-1]
            with S3() as s3:
                s3obj = s3.get(self.s3_file)
                df = pd.read_csv(s3obj.path, index_col=False)
        seqs = df.iloc[:,0].values
        vals = df.iloc[:,1].values

        # Load model metadata (determine model size)
        with S3() as s3:
            s3obj = s3.get(join(self.weights_path,'metadata.json'))
            metadata = json.loads(s3obj.text)
            
        # Record to registry
        features = df.columns.tolist()[1:]
        if len(features)>1: features = ','.join(features)
        else:               features = features[0]
        self.meta = {"flow":current.flow_name, "id":current.run_id, "data_file":self.file_name, "features":features, "size":metadata['size'], "start":self.begin}
        write_row(self.meta, table="training")

        # Train model
        loss, save_path = ut.fit(seqs, vals, 
                        weights_path = self.weights_path,
                        batch_size = int(self.batch_size), 
                        model_size = self.meta['size'], 
                        end_to_end = True if self.end_to_end.lower()=='true' else False,
                        learning_rate = float(self.learning_rate),
                        save_path = SAVE_PATH)

        # Save metadata file
        print('Saving: ' + join(save_path,'metadata.json'))
        self.meta['finish'] = datetime.now()
        self.meta['mse'] = loss[-1]
        with open(join(save_path,'metadata.json'), 'w') as outfile:
            row = self.meta.copy()
            row['start'] = row['start'].strftime('%m/%d/%y %H:%M:%S')
            row['finish'] = row['finish'].strftime('%m/%d/%y %H:%M:%S')
            row['mse'] = str(row['mse'])
            json.dump(row, outfile)

        # Copy outputs to S3
        print('Copying output files to: ' + 's3://'+BUCKET+'/models/'+current.flow_name+'/'+current.run_id+'/')
        saved_files = [f for f in listdir(save_path) if isfile(join(save_path, f))]
        file_paths = [join(save_path, f) for f in saved_files]
        put_files = tuple(zip(saved_files, file_paths))
        with S3(s3root='s3://'+BUCKET+'/models/'+current.flow_name+'/'+current.run_id+'/') as s3:
            s3.put_files(put_files)

        # Adjust registries
        print('Adjusting registry tables')
        delete_row({k:self.meta[k] for k in ['flow', 'id'] if k in self.meta}, table="training") # delete from training registry
        write_row( {k:self.meta[k] for k in model_columns  if k in self.meta}, table="models") # append to trained registry

        self.next(self.end)

    @step
    def end(self):
        print('TrainUniRep has finished.')


if __name__ == '__main__':
    TrainUniRep()
