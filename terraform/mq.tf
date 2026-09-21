variable "rabbitmq_pass" {
  type      = string
  sensitive = true
}

# resource "aws_security_group" "rabbit" {
#   name   = "resland-rabbit-sg"
#   vpc_id = data.aws_vpc.main.id

#   ingress {
#     from_port   = 5671
#     to_port     = 5671
#     protocol    = "tcp"
#     cidr_blocks = ["0.0.0.0/0"]
#   }

#   ingress {
#     from_port   = 443
#     to_port     = 443
#     protocol    = "tcp"
#     cidr_blocks = ["0.0.0.0/0"]
#   }

#   egress {
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
# }

resource "aws_mq_broker" "rabbit" {
  broker_name                = "resland-rabbit"
  engine_type                = "RabbitMQ"
  engine_version             = "4.3"
  host_instance_type         = "mq.m7g.medium"
  deployment_mode            = "SINGLE_INSTANCE"
  auto_minor_version_upgrade = true
  publicly_accessible        = true

  subnet_ids      = [data.aws_subnet.first_public.id]

  user {
    username = "admin"
    password = var.rabbitmq_pass
  }

  lifecycle {
    ignore_changes = [user]
  }
}
