variable "openrouter_api_key" {
  type = string
}

variable "langsmith_api_key" {
  type = string
}

module "dispatcher" {
  source = "./modules/ecs"

  image             = "690473803923.dkr.ecr.us-east-2.amazonaws.com/api:latest"
  cluster_name      = "resland-live"
  service_name      = "dispatcher"
  vpc_id            = data.aws_vpc.main.id
  subnet_ids        = data.aws_subnets.public.ids
  container_command = ["uv", "run", "dispatcher"]

  environment = {
    S3_RESUME_BUCKET   = var.s3_resume_bucket
    AMQP_URL           = "amqps://resland:${urlencode(var.resland_amqp_password)}@${trimprefix(aws_mq_broker.rabbit_live.instances[0].endpoints[0], "amqps://")}"
    AWS_REGION         = data.aws_region.current.region
    PG_URL             = var.pg_conn_string
    OPENROUTER_API_KEY = var.openrouter_api_key
    LANGSMITH_API_KEY  = var.langsmith_api_key
    PYTHONUNBUFFERED   = "1"
  }
}
