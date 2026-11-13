# rotation-function

AWS's Secrets Manager single-user rotation function for PostgreSQL, installed from the Serverless Application Repository through CloudFormation, using the bootstrap's CloudFormation role: the function's role cannot carry the permissions boundary. See README.md.

## Usage

```hcl
module "rotation_function" {
  source = "git::https://github.com/{platform-owner}/ai-app-platform.git//packages/terraform/modules/rotation-function?ref={commit SHA}" # terraform-v{version}

  # The required inputs below
}
```

The commit is the one a release tag names, taken as [Using a module](../../README.md#using-a-module) describes.

## Inputs

| Name | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | The prefix for the stack and function names; the bootstrap's CloudFormation role may only create roles named {name}-rotation-* and the function {name}-rotation. |
| `application_id` | `string` | No | The Serverless Application Repository application holding AWS's rotation function. |
| `application_version` | `string` | No | The application's semantic version; null for the latest, which should then be pinned. |
| `cloudformation_role_arn` | `string` | Yes | The role CloudFormation uses to install the function, from the bootstrap. See README.md. |
| `region` | `string` | Yes | The region, for the Secrets Manager endpoint the function calls. |
| `subnet_ids` | `list(string)` | Yes | The private subnets the function runs in, to reach the database. |
| `security_group_ids` | `list(string)` | Yes | The function's security groups: allowed to the database, and to HTTPS for Secrets Manager. |
| `kms_key_arn` | `string` | No | The customer-managed key the secrets use, if any, so the function can decrypt them. |

## Outputs

| Name | Description |
|---|---|
| `function_arn` | The rotation function, which each rotated secret names. |
| `application_version` | The version of AWS's application installed; pin it in application_version. |

## Why it is installed through a CloudFormation role

AWS publishes the Secrets Manager single-user rotation function for PostgreSQL as a Serverless Application Repository application, installed by CloudFormation, and its template creates the function's IAM role without a permissions boundary. An application's deploy role can create roles only with the boundary (the template's `12-aws-deployment.md`, account bootstrap), so it cannot install the function itself.

The account bootstrap therefore creates one role without the boundary, which only CloudFormation acting for the account can assume, passed in as `cloudformation_role_arn`. It can create and change only the rotation function's role and function, named for the application, attach only AWS's managed Lambda execution policies to them, and read the application from the Serverless Application Repository. The deploy role can pass it to CloudFormation but cannot change it. The application's version is pinned by `application_version`.

This is a departure from the rule that every role an application's pipelines create carries the boundary. An application using this module records the departure in an ADR of its own.
