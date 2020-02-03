# ScalingTL

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

Clone the model to use for transfer learning
```
git clone https://github.com/elyall/UniRep.git ./models/Unirep/
```

Copy metaflow flow file
```
cp metaflow/flow.py models/UniRep/
cd models/UniRep/
```

Train model
```
python3 train_flow.py run
```
