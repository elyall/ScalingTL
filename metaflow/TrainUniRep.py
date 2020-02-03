from metaflow import FlowSpec, step, S3, batch, retry, conda, current
from UniRep import unirep_train
from db_tools import append_flow
from datetime import datetime
import sqlalchemy

class TrainUniRep(FlowSpec):

    @batch(cpu=4, memory=4000)
    @retry
    @conda(libraries={'pandas':'0.23.4', 'numpy':'1.15.4', 'tensorflow':'1.3'}, python='3.6.8')
    @step
    def start(self):
        self.begin = datetime.now()
        with S3(run=self) as s3:
            seq = s3.get('s3://dataidealist/data/bdata.20130222.mhci.txt').text
        unirep_train(seq, vals)
        self.next(self.end)

    @step
    def end(self):
        append_flow(current.flow_name, current.run_id, self.begin, datetime.datetime.now())
        print('TrainUniRep has finished.')


if __name__ == '__main__':
    TrainUniRep()
