#!/usr/bin/env bash
set -euo pipefail

JOB_NAME="${JOB_NAME:-binance-token-screener}"
SOURCE_DIR="${SOURCE_DIR:-.}"

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

gcloud run jobs deploy "$JOB_NAME" --source "$SOURCE_DIR"
