terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
  backend "s3" {
    bucket = "tnttfstate"
    key    = "resume-builder.tfstate"
    region = "us-east-2"
  }
}

provider "aws" {
  region = "us-east-2"
}
