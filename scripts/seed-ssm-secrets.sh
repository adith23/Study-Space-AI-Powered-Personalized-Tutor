#!/bin/bash
# ============================================================
# Seed SSM Parameter Store with production secrets.
#
# Usage:
#   chmod +x scripts/seed-ssm-secrets.sh
#   AWS_PROFILE=your-profile ./scripts/seed-ssm-secrets.sh
#
# This script creates SecureString parameters that the Lambda
# functions read at cold start via app/core/secrets.py.
# ============================================================

set -euo pipefail

PREFIX="/study-space/production"
REGION="${AWS_REGION:-us-east-1}"

echo "🔐 Seeding SSM parameters under: ${PREFIX}"
echo "   Region: ${REGION}"
echo ""

# ── Helper function ──────────────────────────────────────────
put_secret() {
    local name="$1"
    local value="$2"
    aws ssm put-parameter \
        --name "${PREFIX}/${name}" \
        --value "${value}" \
        --type "SecureString" \
        --overwrite \
        --region "${REGION}" \
        --no-cli-pager
    echo "  ✅ ${PREFIX}/${name}"
}

# ── Database (Neon PostgreSQL) ───────────────────────────────
read -rp "DATABASE_URL: " DB_URL
put_secret "DATABASE_URL" "${DB_URL}"
put_secret "DATABASE_SSL_MODE" "require"

# ── Auth ─────────────────────────────────────────────────────
JWT_SECRET=$(openssl rand -hex 32)
echo "  (Generated JWT_SECRET_KEY: ${JWT_SECRET:0:8}...)"
put_secret "JWT_SECRET_KEY" "${JWT_SECRET}"
put_secret "JWT_ALGORITHM" "HS256"
put_secret "ACCESS_TOKEN_EXPIRE_MINUTES" "60"
put_secret "REFRESH_TOKEN_EXPIRE_DAYS" "7"

# ── AI Keys ──────────────────────────────────────────────────
read -rp "GEMINI_API_KEY: " GEMINI_KEY
put_secret "GEMINI_API_KEY" "${GEMINI_KEY}"

read -rp "PINECONE_API_KEY: " PINE_KEY
put_secret "PINECONE_API_KEY" "${PINE_KEY}"

read -rp "PINECONE_INDEX_HOST: " PINE_HOST
put_secret "PINECONE_INDEX_HOST" "${PINE_HOST}"

read -rp "PINECONE_INDEX_NAME: " PINE_NAME
put_secret "PINECONE_INDEX_NAME" "${PINE_NAME}"

read -rp "PINECONE_ENVIRONMENT: " PINE_ENV
put_secret "PINECONE_ENVIRONMENT" "${PINE_ENV}"

# ── Cloudflare R2 ────────────────────────────────────────────
read -rp "R2_ENDPOINT_URL: " R2_EP
put_secret "R2_ENDPOINT_URL" "${R2_EP}"

read -rp "R2_ACCESS_KEY_ID: " R2_AK
put_secret "R2_ACCESS_KEY_ID" "${R2_AK}"

read -rp "R2_SECRET_ACCESS_KEY: " R2_SK
put_secret "R2_SECRET_ACCESS_KEY" "${R2_SK}"

read -rp "R2_BUCKET_NAME: " R2_BUCKET
put_secret "R2_BUCKET_NAME" "${R2_BUCKET}"

# ── SQS Queue URL (from Terraform output) ───────────────────
read -rp "SQS_QUEUE_URL: " SQS_URL
put_secret "SQS_QUEUE_URL" "${SQS_URL}"

# ── CORS (CloudFront domain) ────────────────────────────────
read -rp "CORS_ORIGINS (comma-separated): " CORS
put_secret "CORS_ORIGINS" "${CORS}"

echo ""
echo "✅ All secrets seeded. Lambda functions will pick them up at next cold start."
echo ""
echo "To verify:"
echo "  aws ssm get-parameters-by-path --path ${PREFIX} --region ${REGION} --with-decryption --no-cli-pager"
