#!/bin/bash

# Firebase + Gemini Live API 対応デプロイスクリプト
# Cloud Run へのデプロイ（本番環境）

set -e

# 色付き出力
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# プロジェクト設定
PROJECT_ID="test-6554c"
REGION="asia-northeast1"
SERVICE_NAME="hera-backend-prod"
IMAGE_NAME="hera-backend"
REGISTRY="asia-northeast1-docker.pkg.dev"
REPOSITORY="hera"

# Firebase設定
FIREBASE_PROJECT_ID="test-6554c"
FIREBASE_STORAGE_BUCKET="test-6554c.firebasestorage.app"

# Gemini API Key取得
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}エラー: GEMINI_API_KEY環境変数が設定されていません${NC}"
    echo "export GEMINI_API_KEY=your-api-key"
    exit 1
fi

echo -e "${BLUE}=== Firebase + Gemini Live API デプロイ ===${NC}"
echo -e "プロジェクトID: ${GREEN}$PROJECT_ID${NC}"
echo -e "サービス名: ${GREEN}$SERVICE_NAME${NC}"
echo -e "リージョン: ${GREEN}$REGION${NC}"
echo -e "Firebase Project: ${GREEN}$FIREBASE_PROJECT_ID${NC}"
echo ""

# Live API機能の有効化確認
echo -e "${YELLOW}Gemini Live API機能を有効化しますか? (yes/no)${NC}"
read -p "> " -r
if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    LIVE_API_ENABLED="enabled"
    echo -e "${GREEN}✅ Live API機能: 有効${NC}"
else
    LIVE_API_ENABLED="disabled"
    echo -e "${BLUE}ℹ️  Live API機能: 無効${NC}"
fi
echo ""

# デプロイ確認
echo -e "${YELLOW}本番環境にデプロイしますか? (yes/no)${NC}"
read -p "> " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "デプロイをキャンセルしました"
    exit 0
fi
echo ""

# 1. Dockerイメージのビルド
echo -e "${BLUE}Step 1/3: Dockerイメージをビルド中...${NC}"
cd backend
docker build -t ${REGISTRY}/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:latest .
echo -e "${GREEN}✅ ビルド完了${NC}"
echo ""

# 2. Artifact Registryにプッシュ
echo -e "${BLUE}Step 2/3: Artifact Registryにプッシュ中...${NC}"
docker push ${REGISTRY}/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:latest
echo -e "${GREEN}✅ プッシュ完了${NC}"
echo ""

# 3. Cloud Runにデプロイ
echo -e "${BLUE}Step 3/3: Cloud Runにデプロイ中...${NC}"

# 環境変数設定
ENV_VARS="SESSION_TYPE=firebase"
ENV_VARS="${ENV_VARS},STORAGE_MODE=firebase"
ENV_VARS="${ENV_VARS},FLASK_DEBUG=False"
ENV_VARS="${ENV_VARS},ALLOWED_ORIGINS=*"
ENV_VARS="${ENV_VARS},FIREBASE_PROJECT_ID=${FIREBASE_PROJECT_ID}"
ENV_VARS="${ENV_VARS},FIREBASE_STORAGE_BUCKET=${FIREBASE_STORAGE_BUCKET}"
ENV_VARS="${ENV_VARS},GEMINI_LIVE_MODE=${LIVE_API_ENABLED}"

# Live API有効時の追加設定
if [ "$LIVE_API_ENABLED" = "enabled" ]; then
    ENV_VARS="${ENV_VARS},GEMINI_LIVE_MODEL=gemini-2.0-flash-live-preview-04-09"
    ENV_VARS="${ENV_VARS},AUDIO_INPUT_ENABLED=true"
    ENV_VARS="${ENV_VARS},AUDIO_INPUT_SAMPLE_RATE=16000"
    ENV_VARS="${ENV_VARS},AUDIO_OUTPUT_SAMPLE_RATE=24000"
    ENV_VARS="${ENV_VARS},AUDIO_CHUNK_SIZE_MS=100"
fi

# Cloud Runデプロイ
gcloud run deploy ${SERVICE_NAME} \
    --image=${REGISTRY}/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:latest \
    --platform=managed \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --service-account=firebase-adminsdk-1uma3@${PROJECT_ID}.iam.gserviceaccount.com \
    --set-env-vars="${ENV_VARS}" \
    --set-secrets="GEMINI_API_KEY=gemini-api-key-prod:latest" \
    --port=8080 \
    --cpu=1 \
    --memory=512Mi \
    --timeout=300 \
    --min-instances=0 \
    --max-instances=10 \
    --allow-unauthenticated

cd ..

# デプロイ完了
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --format='value(status.url)')

echo ""
echo -e "${GREEN}=== デプロイ完了 ===${NC}"
echo -e "サービスURL: ${BLUE}${SERVICE_URL}${NC}"
echo ""
echo -e "${YELLOW}動作確認:${NC}"
echo -e "curl ${SERVICE_URL}/api/health"
echo ""

if [ "$LIVE_API_ENABLED" = "enabled" ]; then
    echo -e "${GREEN}🎙️  Gemini Live API機能が有効化されています${NC}"
    echo -e "Ephemeralトークン生成エンドポイント:"
    echo -e "POST ${SERVICE_URL}/api/sessions/<session_id>/ephemeral-token"
else
    echo -e "${BLUE}ℹ️  Gemini Live API機能は無効です${NC}"
    echo -e "有効化するには環境変数 GEMINI_LIVE_MODE=enabled を設定してください"
fi
echo ""

# ログ確認コマンド
echo -e "${YELLOW}ログ確認:${NC}"
echo -e "gcloud run services logs read ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID} --limit=20"
echo ""
