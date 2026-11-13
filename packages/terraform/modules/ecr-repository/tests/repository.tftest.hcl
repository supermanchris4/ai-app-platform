# Planned with a mocked provider: no credentials and nothing created.
mock_provider "aws" {}

variables {
  name = "app-dev-api"
}

run "immutable_and_scanned" {
  command = plan

  assert {
    condition     = aws_ecr_repository.this.image_tag_mutability == "IMMUTABLE"
    error_message = "Tags must be immutable, so a tag always names the same build."
  }

  assert {
    condition     = aws_ecr_repository.this.image_scanning_configuration[0].scan_on_push
    error_message = "Every image must be scanned when pushed."
  }
}
