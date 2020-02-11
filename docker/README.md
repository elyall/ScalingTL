Docker is used to build the container environment metaflow is run in on AWS Batch. Currently training is only working on the CPU docker image, and not the GPU docker image. Packaging the Nvidia driver, Cuda8, and cuDNN has proved challenging.

# Update docker daemon runtime
```
sudo systemctl stop docker
dockerd --default-runtime=nvidia
sudo systemctl restart docker
```

# Build DockerFile
CPU version:
```
docker build -f docker/DockerFile.cpu -t unirep-cpu .
```
CURRENTLY NOT WORKING: GPU version:
[Create AMI image from Deep Learning instance](http://steveadams.io/2016/08/03/AMI-to-Docker.html). Take snapshot from AMI, and attach it as a volume to an instance. Then:
```
sudo mount /dev/xvdf1 /mnt
sudo tar zcpP -C /mnt/ . | docker import - ubuntu:ami-066b6ac622d259bd2
docker build -f docker/DockerFile.gpu -t unirep-gpu . # add extra dependencies
```

# Upload container to ECR
Create ECR repository via aws console (e.g. mine is 654599932930.dkr.ecr.us-west-2.amazonaws.com/dataidealist/tf1.3 on us-west-2).
```
aws ecr get-login --region us-west-2 --no-include-email # required once every 12 hours
docker images # list docker images and find 'Image ID' for relevant container
docker tag ############ 654599932930.dkr.ecr.us-west-2.amazonaws.com/dataidealist/tf1.3
docker push 654599932930.dkr.ecr.us-west-2.amazonaws.com/dataidealist/tf1.3
```

Clean up unused layers: `docker system prune`