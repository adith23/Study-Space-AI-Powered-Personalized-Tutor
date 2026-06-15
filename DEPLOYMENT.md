# Deployment Runbook — Study Space AWS Always Free

> Complete step-by-step guide from zero to production. Every AWS service is **Always Free forever**.

---

## Prerequisites

Install these tools locally:

```bash
# AWS CLI v2
# https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

# Terraform >= 1.5
# https://developer.hashicorp.com/terraform/install

# Docker Desktop
# https://www.docker.com/products/docker-desktop/

# Verify installations
aws --version
terraform -version
docker --version
```

Configure AWS CLI:

```bash
aws configure
# Access Key: (from IAM user)
# Secret Key: (from IAM user)
# Region: us-east-1
# Output: json
```

---

## Step 1 — Set Up External Services

### 1.1 Neon Cloud PostgreSQL

1. Go to https://neon.tech → Sign up → Create project
2. Database name: `studyspace`
3. Copy the **pooled** connection string:
   ```
   postgresql://user:pass@ep-xxx.us-east-1.aws.neon.tech/studyspace?sslmode=require
   ```

### 1.2 Cloudflare R2

1. Go to https://dash.cloudflare.com → Workers & Pages → R2
2. Create bucket: `study-space-files`
3. Create R2 API token → Object Read & Write permissions
4. Note:
   - Account ID
   - Access Key ID
   - Secret Access Key
   - Endpoint URL: `https://<account-id>.r2.cloudflarestorage.com`

### 1.3 Pinecone (keep existing)

- Note: API Key, Index Host, Index Name, Environment

### 1.4 Google Gemini (keep existing)

- Note: API Key

---

## Step 2 — Terraform Phase 1 (Infrastructure without Lambda)

Lambda functions need real Docker images in ECR, but ECR repos don't exist yet. So we deploy in **two phases**:

```bash
cd terraform

# Copy and fill in the example tfvars
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` — set any placeholder for image URIs (they won't be used in Phase 1):

```hcl
aws_region   = "us-east-1"
environment  = "production"
project_name = "study-space"

# Temporary placeholders — will be updated before Phase 2
api_image_uri      = "placeholder"
worker_image_uri   = "placeholder"
frontend_image_uri = "placeholder"
```

Run Phase 1 — create **only** ECR, SQS, IAM, and Monitoring (skip Lambda and CloudFront):

```bash
terraform init
terraform apply -target="module.ecr" -target="module.sqs" -target="module.iam" -target="module.monitoring"
```

After Phase 1 completes, get the ECR repo URIs:

```bash
terraform output ecr_api_repo
terraform output ecr_worker_repo
terraform output ecr_frontend_repo
```

## Step 3 — Set Up GitHub Secrets

Before pushing images, configure GitHub Secrets in your repository (Settings → Secrets → Actions):

| Secret Name | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | Your IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | Your IAM user secret key |
| `ECR_API_REPO_URI` | `ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/study-space-api` |
| `ECR_WORKER_REPO_URI` | `ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/study-space-worker` |
| `ECR_FRONTEND_REPO_URI` | `ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/study-space-frontend` |

*(Replace `ACCOUNT_ID` with your AWS Account ID, or use the exact `terraform output ecr_api_repo` values from Step 2.)*

---

## Step 4 — Build & Push Docker Images (via GitHub Actions)

> **No local Docker needed.** GitHub Actions builds and pushes everything.

1. Commit and push your code to GitHub (if not already pushed):

```bash
git add -A
git commit -m "chore: deployment infrastructure"
git push origin main
```

2. Go to your GitHub repo → **Actions** tab → **"Bootstrap — Push Initial Images"** workflow → **Run workflow**

This runs the one-time `.github/workflows/bootstrap.yml` which builds all 3 Docker images and pushes them to ECR Private — **without** trying to update Lambda functions (since they don't exist yet).

3. Wait for the workflow to complete (green ✅).

---

## Step 5 — Terraform Phase 2 (Lambda + CloudFront)

Update `terraform.tfvars` with the **real** ECR Private image URIs:

```hcl
api_image_uri      = "ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/study-space-api:latest"
worker_image_uri   = "ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/study-space-worker:latest"
frontend_image_uri = "ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/study-space-frontend:latest"
```

Run Phase 2 — creates Lambda functions, Function URLs, and CloudFront:

```bash
cd terraform
terraform apply
```

This creates the remaining resources (Lambda functions + CloudFront distribution).

After apply, note the final outputs:

```bash
terraform output cloudfront_url
terraform output cloudfront_distribution_id
```

Add these as GitHub Secrets too:

| Secret Name | Value |
|---|---|
| `CLOUDFRONT_DISTRIBUTION_ID` | From terraform output |
| `CLOUDFRONT_DOMAIN` | From terraform output (without `https://`) |

---

## Step 6 — Seed SSM Secrets

```bash
chmod +x scripts/seed-ssm-secrets.sh
./scripts/seed-ssm-secrets.sh
```

The script will prompt for each secret interactively.

**Verify:**

```bash
aws ssm get-parameters-by-path \
  --path /study-space/production \
  --region us-east-1 \
  --with-decryption \
  --no-cli-pager
```

---

## Step 7 — Database Migration

```bash
cd backend

# One-time Alembic setup
pip install alembic
alembic init alembic

# Edit alembic/env.py to use your DATABASE_URL
# Then:
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

---

## Step 8 — Verify Deployment

```bash
CF_URL=$(terraform -chdir=terraform output -raw cloudfront_url)

# Health check
curl -sf "${CF_URL}/health"
# Expected: {"status":"healthy","version":"1.0.0","environment":"production"}

# Frontend
curl -sf "${CF_URL}/" | head -20

# API docs
echo "Docs: ${CF_URL}/api/v1/docs"

# Check CloudWatch logs
aws logs tail /aws/lambda/study-space-production-api --follow
```

---

After all secrets are configured (Steps 3 & 5), **every push to `main` will automatically deploy** via the CD pipeline (`cd.yml`).

---

## Troubleshooting

### Cold Starts Are Slow (5-15s)

This is expected for Docker-based Lambda functions. Mitigations:
1. CloudFront caches static assets → most requests don't hit Lambda
2. Health check endpoint has 10s CloudFront cache → keeps the function warm
3. If unacceptable, uncomment provisioned concurrency in `terraform/modules/lambda/main.tf` (not free)

### Lambda Timeout Errors

```bash
# Check CloudWatch logs
aws logs tail /aws/lambda/study-space-production-worker --follow

# Increase timeout in terraform/modules/lambda/main.tf
# Worker is already set to 900s (15-min max)
```

### SQS Dead Letter Queue Not Empty

```bash
# Check DLQ messages
aws sqs receive-message \
  --queue-url $(terraform -chdir=terraform output -raw sqs_dlq_url) \
  --max-number-of-messages 10 \
  --no-cli-pager
```

### Neon Database Connection Issues

```bash
# Neon auto-suspends after 5 minutes of inactivity.
# pool_pre_ping=True in database.py detects stale connections.
# If issues persist, check Neon dashboard for compute status.
```

### CloudFront Not Serving Latest

```bash
# Invalidate cache
aws cloudfront create-invalidation \
  --distribution-id $(terraform -chdir=terraform output -raw cloudfront_distribution_id) \
  --paths "/*" \
  --no-cli-pager
```

### Free Tier Usage Monitor

```bash
# Check Lambda usage
aws lambda get-account-settings --no-cli-pager

# Or use the CloudWatch Logs Insights query:
# See scripts/cloudwatch-queries.md → Query #10
```

---

## Operational Checklist

### Daily

- [ ] Check CloudWatch alarms dashboard
- [ ] Verify DLQ is empty

### Weekly

- [ ] Review CloudWatch Logs Insights for error patterns
- [ ] Check Lambda free tier usage (AWS Billing → Free Tier)
- [ ] Verify Neon storage usage < 0.5 GB

### Monthly

- [ ] Run `pip-audit` and `npm audit` locally
- [ ] Review Lambda memory usage vs allocation
- [ ] Check R2 storage usage < 10 GB
- [ ] Review SQS request count < 1M

---

## Architecture Summary

```
Internet → CloudFront (CDN, TLS, Security Headers)
           ├── /api/*     → API Lambda (FastAPI, 512MB, 5min)
           │                 ├── Neon PostgreSQL (SSL)
           │                 ├── Pinecone (vectors)
           │                 ├── Gemini API (AI)
           │                 └── SQS → Worker Lambda (1GB, 15min)
           │                            ├── Docling (document processing)
           │                            ├── R2 (file storage)
           │                            └── FFmpeg (video generation)
           ├── /*          → Frontend Lambda (Next.js SSR, 256MB)
           └── /_next/static/* → 30-day cache (hashed filenames)
```

**Total monthly cost: $0 — forever.**
