output "ecr_repository_url" {
  value       = aws_ecr_repository.this.repository_url
  description = "Push images here, then set the module's image variable."
}

output "cluster_name" {
  value = aws_ecs_cluster.this.name
}

output "service_name" {
  value = aws_ecs_service.this.name
}

output "task_role_arn" {
  value       = aws_iam_role.task.arn
  description = "Attach additional policies here if the app needs AWS API access."
}

output "task_role_name" {
  value       = aws_iam_role.task.name
  description = "Role name, for aws_iam_role_policy / aws_iam_role_policy_attachment."
}

output "security_group_id" {
  value = aws_security_group.this.id
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.this.name
}

output "lb_dns_name" {
  value       = var.enable_load_balancer ? aws_lb.this[0].dns_name : null
  description = "ALB DNS name — use for a Route53 alias record."
}

output "lb_zone_id" {
  value       = var.enable_load_balancer ? aws_lb.this[0].zone_id : null
  description = "ALB hosted zone ID — use for a Route53 alias record."
}

output "lb_arn" {
  value = var.enable_load_balancer ? aws_lb.this[0].arn : null
}
