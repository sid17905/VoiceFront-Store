# Terraform — VoiceFront Store

## What is provisioned here

| File | Resources |
|---|---|
| `main.tf` | AWS provider, version constraints |
| `variables.tf` | region, environment, bucket name |
| `s3_cloudfront.tf` | private S3 bucket, public-access block, versioning, SSE, lifecycle, CloudFront distribution, OAC, bucket policy scoped to `storefronts/*` |

The bucket is **private**. Objects are served only through CloudFront using an
Origin Access Control. There is no public bucket policy.

## What is deliberately NOT provisioned

`ec2.tf`, `rds.tf`, `elasticache.tf` and `networking.tf` were previously
checked in as **0-byte files**. They have been deleted: an empty file implies
infrastructure that does not exist. For semester 1:

- **Compute:** services run in Docker Compose locally. Production hosting is
  not part of this scope.
- **Database / Redis:** persistence is a SQLite file in `qa-service`
  (`core/history.py`). No RDS or ElastiCache is provisioned.
- **Networking:** no VPC, subnets or security groups are declared.

If those become necessary, add a file *with resources in it* and update this
table and `docs/PROJECT_REPORT_BE.md` §3.7 at the same time.

## Usage

```bash
cd infra/terraform
terraform init
terraform validate
terraform plan \
  -var="bucket_name=voicefront-storefronts-dev" \
  -var="environment=dev"
```

`terraform apply` is a **human action** (decision D-05). Do not run it from CI.

## State

No remote backend is configured. State is local. Before a shared or production
run, add an S3 backend with locking and record the bucket here.

## Custom domain (not done)

`viewer_certificate` uses the default `*.cloudfront.net` certificate. A custom
domain requires an ACM certificate **in us-east-1**, a DNS record, and
`aliases` on the distribution. Record the certificate ARN here when it exists.
