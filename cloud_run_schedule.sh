#!/usr/bin/env bash
set -euo pipefail

JOB_NAME="${JOB_NAME:-binance-token-screener}"
SCHEDULE_NAME="${SCHEDULE_NAME:-${JOB_NAME}-daily}"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_EMAIL:-}"

PROJECT_ID="$(gcloud config get-value project 2>/dev/null || true)"
REGION="$(gcloud config get-value run/region 2>/dev/null || true)"

if [[ -z "$PROJECT_ID" ]]; then
  echo "gcloud project 未设置。请先运行: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi

if [[ -z "$REGION" ]]; then
  echo "Cloud Run region 未设置。请先运行: gcloud config set run/region asia-east1"
  exit 1
fi

if [[ -z "$SERVICE_ACCOUNT_EMAIL" ]]; then
  echo "请设置 SERVICE_ACCOUNT_EMAIL，用于 Cloud Scheduler 触发 Cloud Run Job"
  exit 1
fi

RUN_URI="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run"

gcloud scheduler jobs create http "$SCHEDULE_NAME" \
  --schedule "55 7 * * *" \
  --time-zone "Asia/Shanghai" \
  --uri "$RUN_URI" \
  --http-method POST \
  --oauth-service-account-email "$SERVICE_ACCOUNT_EMAIL" \
  --oauth-token-scope "https://www.googleapis.com/auth/cloud-platform" \
  --location "$REGION"
