output "arn" {
  description = "The load balancer's ARN, which a CloudFront VPC origin names."
  value       = aws_lb.this.arn
}

output "dns_name" {
  description = "The load balancer's DNS name."
  value       = aws_lb.this.dns_name
}

output "arn_suffix" {
  description = "The load balancer's ARN suffix, which CloudWatch metrics name."
  value       = aws_lb.this.arn_suffix
}

output "target_group_arn" {
  description = "The target group the service registers its tasks in."
  value       = aws_lb_target_group.this.arn
}

output "target_group_arn_suffix" {
  description = "The target group's ARN suffix, which CloudWatch metrics name."
  value       = aws_lb_target_group.this.arn_suffix
}
