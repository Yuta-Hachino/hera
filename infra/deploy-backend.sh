#!/bin/bash
set -e

echo "=== Backend Cloud Run デプロイ開始（修正版） ==="

docker run --rm -v /Users/user/dev/hera/backend/firebase-service-account.json:/key.json google/cloud-sdk:latest bash -c "
    gcloud auth activate-service-account --key-file=/key.json 2>/dev/null && \
    gcloud run deploy hera-backend-prod \
      --image=asia-northeast1-docker.pkg.dev/test-6554c/hera/hera-backend:latest \
      --platform=managed \
      --region=asia-northeast1 \
      --project=test-6554c \
      --service-account=firebase-adminsdk-1uma3@test-6554c.iam.gserviceaccount.com \
      --set-env-vars='SESSION_TYPE=firebase,STORAGE_MODE=firebase,FLASK_DEBUG=False,ALLOWED_ORIGINS=*,FIREBASE_PROJECT_ID=test-6554c,FIREBASE_STORAGE_BUCKET=test-6554c.appspot.com' \
      --set-secrets='GEMINI_API_KEY=gemini-api-key-prod:latest' \
      --port=8080 \
      --cpu=1 \
      --memory=512Mi \
      --timeout=300 \
      --min-instances=0 \
      --max-instances=10 \
      --allow-unauthenticated
"

echo ""
echo "=== Backend デプロイ完了 ==="
