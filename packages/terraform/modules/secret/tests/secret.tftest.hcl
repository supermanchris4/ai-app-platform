# Planned with a mocked provider: no credentials and nothing created.
mock_provider "aws" {}

variables {
  name                  = "app-dev/database/runtime"
  description           = "The runtime user's credentials"
  rotate                = true
  rotation_function_arn = "arn:aws:lambda:ap-southeast-2:111122223333:function:app-dev-rotation"
  rotation_days         = 90
}

run "created_without_a_value_and_rotated_later" {
  command = plan

  assert {
    condition     = !aws_secretsmanager_secret_rotation.this[0].rotate_immediately
    error_message = "Rotation must not start until the secret has a value."
  }

  assert {
    condition     = aws_secretsmanager_secret_rotation.this[0].rotation_rules[0].automatically_after_days == 90
    error_message = "The secret must rotate every rotation_days."
  }
}
