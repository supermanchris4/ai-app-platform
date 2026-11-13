output "vpc_id" {
  description = "The VPC, given to each application's configuration as vpc_id."
  value       = aws_vpc.this.id
}

output "private_subnet_ids" {
  description = "The two private subnets, given to each application as app_subnet_ids and lb_subnet_ids."
  value       = aws_subnet.private[*].id
}
