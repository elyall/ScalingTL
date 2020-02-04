# ScalingTL

This project uses [Metaflow](https://metaflow.org/) on [AWS Batch](https://aws.amazon.com/batch/) to scale training of [UniRep](https://github.com/churchlab/UniRep) in a reproducible, version controlled fashion. This training platform is served to the end user via a [Dash](https://plot.ly/dash/) frontend.

To get started:

Clone this repository
```
git clone https://github.com/elyall/ScalingTL
cd ScalingTL
```

Install the requirements
```
pip3 install -r requirements.txt
```

Configure your AWS account
```
aws configure
```

Set up Batch compute environment and configure metaflow
```
metaflow configure aws
```


Clone the model to use for transfer learning
```
git clone https://github.com/elyall/UniRep.git ./models/Unirep/
```

Copy metaflow flow file
```
cp metaflow/TrainUniRep.py models/UniRep/
cd models/UniRep/
```

Train model
```
python3 TrainUniRep.py run
```
