output "address" {
  description = "The instance's host name, the API's DATABASE_HOST."
  value       = aws_db_instance.this.address
}

output "port" {
  description = "The instance's port."
  value       = aws_db_instance.this.port
}

output "database_name" {
  description = "The database's name, the API's DATABASE_NAME."
  value       = aws_db_instance.this.db_name
}

output "identifier" {
  description = "The instance's identifier, which CloudWatch metrics name."
  value       = aws_db_instance.this.identifier
}

output "master_user_secret_arn" {
  description = "The secret RDS keeps the master user's credentials in, which only the database initialisation task reads."
  value       = aws_db_instance.this.master_user_secret[0].secret_arn
}
