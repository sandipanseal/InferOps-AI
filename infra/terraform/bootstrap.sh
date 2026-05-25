#!/usr/bin/env bash
#
# One-time bootstrap for the Terraform S3 backend.
#
# The S3 bucket that holds the Terraform state file must exist *before*
# `terraform init` can run (chicken-and-egg). This script creates it.
#
# Usage:
#   AWS_PROFILE=inferops ./bootstrap.sh
#
# Idempotent — re-running is safe.

set -euo pipefail

BUCKET="${TF_STATE_BUCKET:-inferops-terraform-state}"
REGION="${AWS_REGION:-eu-central-1}"

echo "→ Bucket: $BUCKET"
echo "→ Region: $REGION"

if aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  echo "✓ State bucket already exists — nothing to do."
  exit 0
fi

echo "→ Creating state bucket…"
if [ "$REGION" = "us-east-1" ]; then
  # us-east-1 is the one region that rejects LocationConstraint
  aws s3api create-bucket --bucket "$BUCKET" --region "$REGION"
else
  aws s3api create-bucket \
    --bucket "$BUCKET" \
    --region "$REGION" \
    --create-bucket-configuration "LocationConstraint=$REGION"
fi

echo "→ Enabling versioning…"
aws s3api put-bucket-versioning \
  --bucket "$BUCKET" \
  --versioning-configuration Status=Enabled

echo "→ Enabling default encryption…"
aws s3api put-bucket-encryption \
  --bucket "$BUCKET" \
  --server-side-encryption-configuration '{
    "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
  }'

echo "→ Blocking all public access…"
aws s3api put-public-access-block \
  --bucket "$BUCKET" \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

echo "✓ State bucket ready. Now run: terraform init"
