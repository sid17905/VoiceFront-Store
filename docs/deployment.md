# VoiceStorefront — Deployment

Two environments: local dev (Docker Compose, everyone's laptop) and AWS (shared staging, used
for demos and the pilot). No separate "production" beyond staging for an academic MVP — don't
build infra you won't use before the deadline.

**Updated per `inference_hosting_plan.md`: Whisper and Llama-3 run on Groq's free API, not
locally and not on a self-hosted GPU box.** This changes what's actually deployed — nothing in
this stack needs a GPU anymore, which is why the AWS side below is CPU-only and free-tier-eligible.

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
    env_file: ../../services/asr-service/.env   # GROQ_API_KEY, no local model weights
    ports: ["8001:8000"]
    depends_on: [postgres]

  nlp-service:
    build: ../../services/nlp-service
    env_file: ../../services/nlp-service/.env   # GROQ_API_KEY + IndicBERT weights (small, local NER only)
    ports: ["8002:8000"]
    depends_on: [postgres]

  layout-service:
    build: ../../services/layout-service
    env_file: ../../services/layout-service/.env
    ports: ["8003:8000"]
    depends_on: [postgres]

  qa-service:
    build: ../../services/qa-service
    env_file: ../../services/qa-service/.env    # GROQ_API_KEY for LLM-assisted repair fallback
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
No multi-GB Whisper/Ollama weights to mount anymore — only IndicBERT (small, CPU-friendly) and
CodeBERT (also small) are local. This is a large part of why every teammate's laptop, regardless
of GPU, works fine for local dev now.

## 2. AWS staging architecture — CPU-only, free-tier

No GPU instance anywhere in this diagram. Whisper and Llama-3 calls go out to Groq's API from
whichever service needs them (`asr-service`, `nlp-service`, `qa-service`'s repair fallback).
Everything AWS actually runs is small and free-tier-eligible.

```
Registrar (domain, ~$10/yr) → Route 53 or direct DNS → CloudFront (storefronts CDN) → S3 (published bundles)
                                                              │
                                                              └─ CloudFront (app) → ALB → EC2 t3.micro
                                                                                            ├── asr-service
                                                                                            ├── nlp-service
                                                                                            ├── layout-service
                                                                                            ├── qa-service
                                                                                            └── publish-service
                                                                                      │
                                                                                      ├── RDS Postgres (db.t3.micro, free tier)
                                                                                      └── Redis (run in Docker on the same t3.micro — skip ElastiCache, not worth the cost for pilot scale)
```

All 5 services fit comfortably on a single `t3.micro` (2 vCPU, 1 GB RAM) since none of them are
doing GPU-class work anymore — they're making outbound HTTPS calls to Groq and otherwise doing
light CPU work (Jinja2 rendering, Playwright headless Chromium, FAISS lookups, small IndicBERT
inference). If Playwright's Chromium rendering feels tight on 1 GB RAM during QA runs, step up
to `t3.small` (2 GB RAM) — still free-tier-eligible-adjacent and only a few dollars/month if it
falls outside the tier.

**Costing — see `inference_hosting_plan.md` for the model-inference side; this is the hosting side:**

| Item | Cost |
|---|---|
| EC2 `t3.micro` (all 5 services) | $0 (AWS Free Tier, 12 months) |
| RDS `db.t3.micro` Postgres | $0 (AWS Free Tier, 12 months) |
| S3 (storefront bundles) | $0 (5 GB free tier) |
| CloudFront (CDN + HTTPS via ACM) | $0 (1 TB/month free tier) |
| Domain name | ~$10/year (buy through Namecheap or similar, point DNS at CloudFront — skip Route 53's hosted-zone fee) |

**Total AWS-side cost: ~$10 one-time, for the domain — everything else is free tier.**

## 3. Terraform layout (`infra/terraform/`)
```
infra/terraform/
├── main.tf              # provider config, backend state (S3 + DynamoDB lock)
├── networking.tf         # VPC, subnets, security groups
├── ec2.tf                # t3.micro instance definition (CPU-only — no GPU needed, see inference_hosting_plan.md)
├── rds.tf                # db.t3.micro, free tier
├── s3_cloudfront.tf      # storefront hosting + app CDN + ACM cert for the domain
└── variables.tf
```
(`elasticache.tf` dropped — Redis now runs in Docker on the same `t3.micro` instead of a managed
service, since it's only qa-service's hot cache and doesn't justify the cost at pilot scale.)

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

## 7. One-time self-hosted validation run (Month 5 only)
Per `inference_hosting_plan.md`: daily dev and the pilot both run on Groq's free API, not
self-hosted Whisper/Llama. To back up your framework's "self-hostable" claim for Table 4 with a
real number, rent a `g4dn.xlarge` (T4, 16 GB VRAM) for a few hours in Month 5, run the WER and
schema-F1 benchmarks (`test_wer.py`, `test_schema_f1.py`) against genuinely self-hosted
`faster-whisper` + Ollama, record the results, then terminate the instance. Cost: ~$5–10 for a
handful of hours, not a standing line item. Do not leave this instance running after the
benchmark — there's no ongoing reason to.
