#!/bin/bash
set -e

echo "=== Cloud Build経由でBackendをデプロイ（Firebase + Live API対応） ==="

# Live API機能の有効化確認
LIVE_API_MODE="${1:-enabled}"
echo "Gemini Live API: $LIVE_API_MODE"

# 環境変数設定
ENV_VARS="SESSION_TYPE=firebase,STORAGE_MODE=firebase,FLASK_DEBUG=False,ALLOWED_ORIGINS=*,FIREBASE_PROJECT_ID=test-6554c,FIREBASE_STORAGE_BUCKET=test-6554c.firebasestorage.app,GEMINI_LIVE_MODE=$LIVE_API_MODE"

# Live API有効時の追加設定
if [ "$LIVE_API_MODE" = "enabled" ]; then
    ENV_VARS="${ENV_VARS},GEMINI_LIVE_MODEL=gemini-2.0-flash-live-preview-04-09,AUDIO_INPUT_ENABLED=true,AUDIO_INPUT_SAMPLE_RATE=16000,AUDIO_OUTPUT_SAMPLE_RATE=24000,AUDIO_CHUNK_SIZE_MS=100"
    echo "✅ Live API追加設定: 有効"
else
    echo "ℹ️  Live API: 無効"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/../backend"

docker run --rm -v "$BACKEND_DIR":/workspace -v "$BACKEND_DIR/firebase-service-account.json":/key.json -w /workspace google/cloud-sdk:latest bash -c "
    gcloud auth activate-service-account --key-file=/key.json 2>/dev/null && \
    gcloud run deploy hera-backend-prod \
      --source . \
      --platform=managed \
      --region=asia-northeast1 \
      --project=test-6554c \
      --service-account=firebase-adminsdk-1uma3@test-6554c.iam.gserviceaccount.com \
      --set-env-vars='$ENV_VARS' \
      --set-secrets='GEMINI_API_KEY=gemini-api-key-prod:latest' \
      --port=8080 \
      --cpu=2 \
      --cpu-boost \
      --memory=1Gi \
      --timeout=600 \
      --min-instances=0 \
      --max-instances=10 \
      --allow-unauthenticated
"

echo ""
echo "=== Backend デプロイ完了 ==="
echo ""
echo "サービスURL確認:"
docker run --rm -v /Users/user/dev/hera/backend/firebase-service-account.json:/key.json google/cloud-sdk:latest bash -c "
    gcloud auth activate-service-account --key-file=/key.json 2>/dev/null && \
    gcloud run services describe hera-backend-prod \
      --region=asia-northeast1 \
      --project=test-6554c \
      --format='value(status.url)'
"
