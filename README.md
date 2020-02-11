# ScalingTL: a productionized transfer learning pipeline for UniRep

This project uses [Metaflow](https://metaflow.org/) on [AWS Batch](https://aws.amazon.com/batch/) to scale training of [UniRep](https://github.com/churchlab/UniRep) in a reproducible, version controlled fashion. This training platform is served to the end user via a [Dash](https://plot.ly/dash/) frontend and model metadata is tracked via a [MySQL](https://www.mysql.com/) database.

**Navigate to the [website] to being performing transfer learning with UniRep on your own data on the cloud!**

### Highlights:
1. Simple: transfer learning on new data is started via a few button clicks on the website.
2. Scalable: can scale to as many concurrent jobs as you want to pay for via AWS Batch.
3. Reproducible: all steps of training are version controlled via Metaflow.
4. Transparent: all trained models are available to everyone.

### Use cases:
1. Good for a large org that wants to empower its users or employees to easily build performant models on new data. Not good for a single user building models on their own (better to use Metaflow's python module than a website).
2. Good for training on models that have large opportunities for transfer learning on new datasets with the the same data schema (e.g. [UniRep](https://github.com/churchlab/UniRep), [DeepLabCut](https://github.com/AlexEMG/DeepLabCut), etc.). Not good for training a be-all end-all model on a singular or evolving dataset (the frontend as well as the database of all trained models would be unnecessary).


## Architecture

![alt text][architecture]

## Using this Cloud Service

Navigate to the [website], upload your data or select a preloaded dataset, and initiate training a new model with transfer learning off a previously trained model!


## Installing this Cloud Service For Your Own Use

1. Clone this repository: `git clone https://github.com/elyall/ScalingTL`

2. Build docker container by following [docker/README.md](docker/README.md).

3. Set up Batch compute environment by following [metaflow/cloudformation/README.md](metaflow/cloudformation/README.md).

5. Install database by following [mysql/README.md](mysql/README.md). Place it on an EC2 instance on the metaflow VPC so that batch jobs can easily write to it.

6. Install frontend by following [dash/README.md](dash/README.md). Place it on an EC2 instance on the database's VPC (read: metaflow's VPC) so that it can read/write to it.

7. Navigate to your website, load in a dataset, and perform transfer learning!


## Future Roadmap
1. Build out prediction pipeline.
2. Separate UniRep model from repo to allow starting model to be plug and play.


[website]: https://dataidealist.xyz
[architecture]: https://github.com/elyall/ScalingTL/architecture.png