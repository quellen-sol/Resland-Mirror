data "aws_caller_identity" "current" {}

# The api and dispatcher services both run the one image deploy.sh pushes.
locals {
  api_image = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${data.aws_region.current.region}.amazonaws.com/api:latest"
}
