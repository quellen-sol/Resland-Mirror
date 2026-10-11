resource "aws_security_group" "lb" {
  count = var.enable_load_balancer ? 1 : 0

  name   = "${var.service_name}-lb"
  vpc_id = var.vpc_id

  dynamic "ingress" {
    for_each = var.certificate_arn != null ? [80, 443] : [80]
    content {
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = var.lb_ingress_cidr_blocks
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_lb" "this" {
  count = var.enable_load_balancer ? 1 : 0

  name               = "${var.service_name}-lb"
  internal           = var.lb_internal
  load_balancer_type = "application"
  security_groups    = [aws_security_group.lb[0].id]
  subnets            = var.subnet_ids
}

resource "aws_lb_target_group" "this" {
  count = var.enable_load_balancer ? 1 : 0

  name                 = "${var.service_name}-tg"
  port                 = var.container_port
  protocol             = "HTTP"
  vpc_id               = var.vpc_id
  target_type          = "ip"
  deregistration_delay = 30

  health_check {
    path              = var.health_check_path
    matcher           = "200-399"
    healthy_threshold = 2
  }

  lifecycle {
    precondition {
      condition     = var.container_port != null
      error_message = "container_port must be set when enable_load_balancer is true."
    }
  }
}

resource "aws_lb_listener" "http" {
  count = var.enable_load_balancer ? 1 : 0

  load_balancer_arn = aws_lb.this[0].arn
  port              = 80
  protocol          = "HTTP"

  dynamic "default_action" {
    for_each = var.certificate_arn == null ? [1] : []
    content {
      type             = "forward"
      target_group_arn = aws_lb_target_group.this[0].arn
    }
  }

  dynamic "default_action" {
    for_each = var.certificate_arn != null ? [1] : []
    content {
      type = "redirect"
      redirect {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  }
}

resource "aws_lb_listener" "https" {
  count = var.enable_load_balancer && var.certificate_arn != null ? 1 : 0

  load_balancer_arn = aws_lb.this[0].arn
  port              = 443
  protocol          = "HTTPS"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this[0].arn
  }
}
