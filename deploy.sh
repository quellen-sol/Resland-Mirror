#!/bin/bash

AWS_REGION=us-east-2
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}
MY_DIR=$(dirname $0)

# build image
cd $MY_DIR
docker build -t resland .

# push to ecr
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

docker tag resland:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/api:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/api:latest

# run task def update with `:latest`
aws ecs update-service --cluster resland-live --service api --force-new-deployment
aws ecs update-service --cluster resland-live --service dispatcher --force-new-deployment
