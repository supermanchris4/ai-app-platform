# Planned with a mocked provider: no credentials and nothing created.
mock_provider "aws" {
  mock_data "aws_iam_policy_document" {
    defaults = { json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}" }
  }
}

variables {
  name              = "app-dev-uploads-111122223333"
  expire_after_days = 30
}

run "private_and_expiring" {
  command = plan

  assert {
    condition = alltrue([
      aws_s3_bucket_public_access_block.this.block_public_acls,
      aws_s3_bucket_public_access_block.this.block_public_policy,
      aws_s3_bucket_public_access_block.this.ignore_public_acls,
      aws_s3_bucket_public_access_block.this.restrict_public_buckets,
    ])
    error_message = "All public access must be blocked."
  }

  assert {
    condition     = aws_s3_bucket_lifecycle_configuration.this.rule[0].status == "Enabled" && aws_s3_bucket_lifecycle_configuration.this.rule[0].expiration[0].days == 30
    error_message = "Objects must be deleted after expire_after_days."
  }
}
