resource "aws_route53_zone" "resland_zone" {
  name = "resland.org"
}

resource "aws_acm_certificate" "resland" {
  domain_name       = "resland.org"
  validation_method = "DNS"
}

resource "aws_acm_certificate" "resland_api" {
  domain_name       = "api.resland.org"
  validation_method = "DNS"
}

resource "aws_route53_record" "resland_api" {
  for_each = {
    for dvo in aws_acm_certificate.resland_api.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.resland_zone.zone_id
}

resource "aws_route53_record" "resland" {
  for_each = {
    for dvo in aws_acm_certificate.resland.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.resland_zone.zone_id
}

resource "aws_acm_certificate_validation" "resland" {
  certificate_arn         = aws_acm_certificate.resland.arn
  validation_record_fqdns = [for record in aws_route53_record.resland : record.fqdn]
}

resource "aws_acm_certificate_validation" "resland_api" {
  certificate_arn         = aws_acm_certificate.resland_api.arn
  validation_record_fqdns = [for record in aws_route53_record.resland_api : record.fqdn]
}
