# A Resource Group holding every resource that carries the given tags, so an application's resources
# in one environment can be found and reviewed together (the template's 12-aws-deployment.md#principles).
resource "aws_resourcegroups_group" "this" {
  name        = var.name
  description = var.description

  resource_query {
    query = jsonencode({
      ResourceTypeFilters = ["AWS::AllSupported"]
      TagFilters = [
        for key, value in var.tag_filters : { Key = key, Values = [value] }
      ]
    })
  }
}
