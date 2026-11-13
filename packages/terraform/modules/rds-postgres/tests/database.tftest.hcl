# Planned with a mocked provider: no credentials and nothing created.
mock_provider "aws" {}

variables {
  identifier            = "app-dev"
  database_name         = "app"
  instance_class        = "db.t4g.micro"
  allocated_storage     = 20
  subnet_ids            = ["subnet-0123456789abcdef0", "subnet-0123456789abcdef1"]
  security_group_ids    = ["sg-0123456789abcdef0"]
  backup_retention_days = 7
  deletion_protection   = true
}

run "private_encrypted_and_tls_only" {
  command = plan

  assert {
    condition     = !aws_db_instance.this.publicly_accessible
    error_message = "The database must not be publicly accessible."
  }

  assert {
    condition     = aws_db_instance.this.storage_encrypted
    error_message = "The database must be encrypted at rest."
  }

  assert {
    condition     = aws_db_instance.this.manage_master_user_password && aws_db_instance.this.password == null
    error_message = "RDS must manage the master password; Terraform must never hold one."
  }

  assert {
    condition     = anytrue([for parameter in aws_db_parameter_group.this.parameter : parameter.name == "rds.force_ssl" && parameter.value == "1"])
    error_message = "Connections without TLS must be refused."
  }

  assert {
    condition     = anytrue([for parameter in aws_db_parameter_group.this.parameter : parameter.name == "ssl_min_protocol_version" && parameter.value == "TLSv1.2"])
    error_message = "Connections must use TLS 1.2 or later."
  }

  assert {
    condition     = !aws_db_instance.this.skip_final_snapshot && aws_db_instance.this.deletion_protection
    error_message = "A protected database must keep a final snapshot."
  }
}
