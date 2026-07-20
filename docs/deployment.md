# VoiceStorefront — Deployment

Two environments: local dev (Docker Compose, everyone's laptop) and AWS (shared staging, used
for demos and the pilot). No separate "production" beyond staging for an academic MVP — don't
build infra you won't use before the deadline.

## 1. Local development — `infra/docker/docker-compose.dev.yml`

```yaml
services:
  postgres:
    image: postgres:16
    environment: { POSTGRES_DB: voicestorefront, POSTGRES_PASSWORD: dev }
    ports: ["5432:5432"]

  redis:
    image: redis:7
    ports: ["6379:6379"]

  asr-service:
    build: ../../services/asr-service
    env_file: ../../services/asr-service/.env
    ports: ["8001:8000"]
    depends_on: [postgres]

  nlp-service:
    build: ../../services/nlp-service
    env_file: ../../services/nlp-service/.env
    ports: ["8002:8000"]
    depends_on: [postgres]

  layout-service:
    build: ../../services/layout-service
    env_file: ../../services/layout-service/.env
    ports: ["8003:8000"]
    depends_on: [postgres]

  qa-service:
    build: ../../services/qa-service
    env_file: ../../services/qa-service/.env
    ports: ["8004:8000"]
    depends_on: [postgres, redis]

  publish-service:
    build: ../../services/publish-service
    env_file: ../../services/publish-service/.env
    ports: ["8005:8000"]
    depends_on: [postgres]

  web:
    build: ../../apps/web
    env_file: ../../apps/web/.env.local
    ports: ["3000:3000"]
    depends_on: [asr-service, nlp-service, layout-service, qa-service, publish-service]
```

Bring the whole stack up: `docker compose -f infra/docker/docker-compose.dev.yml up --build`.
Whisper/IndicBERT model weights are large — mount them as a volume rather than baking into the
image, or every teammate's `docker build` becomes a multi-GB download.

## 2. AWS staging architecture

Aligned with Table 4 of the submitted (mentor-approved) framework: plain EC2, not ECS. This is
the assumption going forward in this file and in `files.md` — if the team later decides
containers-on-ECS are worth the divergence from the approved document, that's a deliberate
conversation to have with your mentors first, not a default to slide into via infra tooling.

```
Route 53 → CloudFront (storefronts CDN) → S3 (published bundles)
                     │
                     └─ CloudFront (app) → ALB → EC2 instances (one per service, or co-located
                                                   by resource profile — see note below)
                                                    ├── asr-service
                                                    ├── nlp-service
                                                    ├── layout-service
                                                    ├── qa-service
                                                    └── publish-service
                                              │
                                              ├── RDS Postgres (single instance, no read replica for MVP)
                                              └── ElastiCache Redis
```

Practical note for a 4-person team on raw EC2: don't run 5 separate instances if budget/ops time
is tight. `asr-service` and `nlp-service` are the GPU/CPU-heavy pair (Whisper, IndicBERT, LLM
inference) and are reasonable to co-locate on one larger instance; `layout-service`,
`qa-service`, and `publish-service` are comparatively lightweight and can share a second instance.
Each service still runs as its own systemd-managed process with its own port, so the service
boundary in code doesn't change — only the physical grouping does. Document whichever grouping
you pick in `infra/terraform/variables.tf` so it isn't tribal knowledge.

## 3. Terraform layout (`infra/terraform/`)
```
infra/terraform/
├── main.tf              # provider config, backend state (S3 + DynamoDB lock)
├── networking.tf         # VPC, subnets, security groups
├── ec2.tf                # instance definitions, security groups, systemd unit provisioning
├── rds.tf
├── elasticache.tf
├── s3_cloudfront.tf      # storefront hosting + app CDN
└── variables.tf
```

## 4. CI/CD (`infra/ci-cd/`, GitHub Actions)
- One workflow per service: `test → build image → push to ECR → pull + restart container on the
  target EC2 instance (via SSM Run Command, not ECS orchestration)` — triggered only on changes
  to that service's path (path-filtered triggers), so one person's ASR change doesn't redeploy QA.
  Still using Docker images for build reproducibility, just not container orchestration.
- `packages/schemas` changes trigger a cross-service check workflow (per `integration.md` §5) before
  any individual service workflow is allowed to deploy.
- Nightly workflow runs `tests/e2e/` against staging.

## 5. Rollback policy
Keep the previous deployed build artifact (tagged release, not just `latest`) for each service on
the EC2 instance or in S3; rollback is `systemctl stop {service} && ln -sfn {previous-release-dir}
current && systemctl start {service}` — document the exact command sequence per service in your
runbook, don't rely on remembering it during a live demo failure.

## 6. What NOT to automate for this project
Blue/green deployment, multi-region failover, autoscaling policies tuned for real traffic — none of
this matters for a 50-user pilot cohort. Time spent here is time not spent hitting the WER/F1/WCAG
targets your mentors will actually grade.
