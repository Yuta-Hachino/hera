#!/bin/bash
set -e

echo "=== Frontendをデプロイ（Firebase + Live API対応） ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/../frontend"

# Firebase API Keyをシークレットから取得
echo "Firebase APIキーを取得中..."
FIREBASE_API_KEY=$(docker run --rm -v "$SCRIPT_DIR/../backend/firebase-service-account.json:/key.json" google/cloud-sdk:latest bash -c "
    gcloud auth activate-service-account --key-file=/key.json 2>/dev/null && \
    gcloud secrets versions access latest --secret=firebase-api-key-prod --project=test-6554c
")

echo "Firebase API Key取得完了"

# フロントエンドをデプロイ（ビルド引数付き）
docker run --rm -v "$FRONTEND_DIR":/workspace -v "$SCRIPT_DIR/../backend/firebase-service-account.json":/key.json -w /workspace google/cloud-sdk:latest bash -c "
    gcloud auth activate-service-account --key-file=/key.json 2>/dev/null && \
    cat > .env.production <<EOF
NEXT_PUBLIC_API_URL=https://hera-backend-prod-716580137550.asia-northeast1.run.app
NEXT_PUBLIC_FIREBASE_API_KEY=$FIREBASE_API_KEY
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=test-6554c.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=test-6554c
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=test-6554c.firebasestorage.app
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=716580137550
NEXT_PUBLIC_FIREBASE_APP_ID=1:716580137550:web:754d37c7f4f51b3363b11f
EOF
    echo '.env.production created:' && cat .env.production
    gcloud run deploy hera-frontend-prod \
      --source . \
      --platform=managed \
      --region=asia-northeast1 \
      --project=test-6554c \
      --allow-unauthenticated \
      --port=3000 \
      --cpu=1 \
      --memory=512Mi \
      --timeout=60 \
      --min-instances=0 \
      --max-instances=10
"

echo ""
echo "=== Frontend デプロイ完了 ==="
echo ""
echo "サービスURL確認:"
docker run --rm -v "$SCRIPT_DIR/../backend/firebase-service-account.json:/key.json" google/cloud-sdk:latest bash -c "
    gcloud auth activate-service-account --key-file=/key.json 2>/dev/null && \
    gcloud run services describe hera-frontend-prod \
      --region=asia-northeast1 \
      --project=test-6554c \
      --format='value(status.url)'
"