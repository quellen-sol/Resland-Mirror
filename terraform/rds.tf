variable "pg_password" {
    type = string
    sensitive = true
}

resource "aws_db_subnet_group" "db_live" {
  name       = "db-live-subnet-group"
  subnet_ids = data.aws_subnets.public.ids
}

resource "aws_security_group" "db_live" {
  vpc_id = data.aws_vpc.main.id

  ingress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port = 5432
    to_port = 5432
    protocol = "tcp"
  }

  egress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port = 0
    to_port = 0
    protocol = "-1"
  }
}

resource "aws_db_instance" "db-live" {
    engine = "postgres"
    username = "postgres"
    password = var.pg_password

    apply_immediately = true
    publicly_accessible = true

    instance_class = "db.m7g.large"
    storage_type = "gp3"
    allocated_storage = 20
    max_allocated_storage = 200

    db_subnet_group_name = aws_db_subnet_group.db_live.name
    vpc_security_group_ids = [aws_security_group.db_live.id]

    backup_retention_period = 3
}
