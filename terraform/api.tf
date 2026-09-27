variable "s3_resume_bucket" {
  type      = string
  sensitive = true
}

variable "pg_conn_string" {
  type      = string
  sensitive = true
}

variable "auth0_domain" {
  type = string
}

variable "auth0_audience" {
  type = string
}

variable "stripe_secret_key" {
  type      = string
  sensitive = true
}

variable "stripe_webhook_secret" {
  type      = string
  sensitive = true
}

variable "resland_amqp_password" {
  type        = string
  sensitive   = true
  description = "Password for the 'resland' RabbitMQ user (created in the RabbitMQ console, not via AWS)."
}

module "api" {
  source = "./modules/ecs"

  image                = "690473803923.dkr.ecr.us-east-2.amazonaws.com/api:latest"
  cluster_name         = "resland-live"
  service_name         = "api"
  vpc_id               = data.aws_vpc.main.id
  subnet_ids           = data.aws_subnets.public.ids
  container_port       = 3001
  enable_load_balancer = true
  health_check_path    = "/docs"
  container_command    = ["uv", "run", "api"]
  certificate_arn      = aws_acm_certificate.resland_api.arn

  environment = {
    S3_RESUME_BUCKET      = var.s3_resume_bucket
    AMQP_URL              = "amqps://resland:${urlencode(var.resland_amqp_password)}@${trimprefix(aws_mq_broker.rabbit_live.instances[0].endpoints[0], "amqps://")}"
    AWS_REGION            = data.aws_region.current.region
    PG_URL                = var.pg_conn_string
    AUTH0_DOMAIN          = var.auth0_domain
    AUTH0_AUDIENCE        = var.auth0_audience
    STRIPE_SECRET_KEY     = var.stripe_secret_key
    STRIPE_WEBHOOK_SECRET = var.stripe_webhook_secret
    FRONTEND_BASE_URL     = "https://resland.org"
    # Seeds site_settings.maintenance_mode on first read; /admin owns it after.
    MAINTENANCE_MODE      = "1"
    PYTHONUNBUFFERED      = "1"
  }
}
