variable "main_vpc_id" {
  type      = string
  sensitive = true
}

variable "first_subnet" {
  type      = string
  sensitive = true
}

data "aws_vpc" "main" {
  id = var.main_vpc_id
}

data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }
}

data "aws_subnet" "first_public" {
  id = var.first_subnet
}
