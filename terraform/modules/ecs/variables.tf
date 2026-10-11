variable "service_name" {
  type        = string
  description = "Name used for the ECR repo, ECS service, task family, log group, and cluster (unless cluster_name is set)."
}

variable "cluster_name" {
  type        = string
  default     = null
  description = "ECS cluster name. Defaults to service_name."
}

variable "vpc_id" {
  type        = string
  description = "VPC for the service security group."
}

variable "subnet_ids" {
  type        = list(string)
  description = "Subnets for the Fargate tasks (awsvpc networking)."
}

variable "image" {
  type        = string
  default     = "public.ecr.aws/docker/library/nginx:latest"
  description = "Container image. Defaults to a public nginx placeholder until you push to the ECR repo."
}

variable "container_port" {
  type        = number
  default     = null
  description = "Port the container listens on; adds the portMapping and SG ingress rule. Omit for worker services (e.g. dispatcher) that don't accept inbound traffic."
}

variable "cpu" {
  type        = number
  default     = 256
  description = "Fargate task CPU units."
}

variable "memory" {
  type        = number
  default     = 512
  description = "Fargate task memory (MiB)."
}

variable "desired_count" {
  type        = number
  default     = 1
  description = "Number of running tasks."
}

variable "assign_public_ip" {
  type        = bool
  default     = true
  description = "Assign public IPs to tasks. Required when running in public subnets without a NAT gateway."
}

variable "environment" {
  type        = map(string)
  default     = {}
  description = "Environment variables injected into the container."
}

variable "ingress_cidr_blocks" {
  type        = list(string)
  default     = ["0.0.0.0/0"]
  description = "CIDRs allowed to reach container_port."
}

variable "log_retention_days" {
  type        = number
  default     = 30
  description = "CloudWatch log retention."
}

variable "enable_load_balancer" {
  type        = bool
  default     = false
  description = "Create an ALB + target group and register the service's tasks. Requires container_port."
}

variable "lb_internal" {
  type        = bool
  default     = false
  description = "Make the load balancer internal (VPC-only) instead of internet-facing."
}

variable "lb_ingress_cidr_blocks" {
  type        = list(string)
  default     = ["0.0.0.0/0"]
  description = "CIDRs allowed to reach the load balancer on ports 80/443."
}

variable "certificate_arn" {
  type        = string
  default     = null
  description = "ACM certificate ARN. When set, port 443 serves HTTPS and port 80 redirects to it."
}

variable "health_check_path" {
  type        = string
  default     = "/"
  description = "Target group health check path. For default FastAPI use /docs (returns 200)."
}

variable "container_command" {
  type = list(string)
  default = null
  description = "Command to run the docker image with, if any"
}
