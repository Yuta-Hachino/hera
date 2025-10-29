#!/bin/bash

# Cloud Run デプロイスクリプト
# 使用方法: ./deploy-cloud-run.sh [frontend|backend|adk|all]

set -e

# 色付き出力
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# デフォルト設定
PROJECT_ID="${GCP_PROJECT_ID}"
REGION="${GCP_REGION:-asia-northeast1}"
FRONTEND_SERVICE="hera-frontend"
BACKEND_SERVICE="hera-backend"
ADK_SERVICE="hera-adk"

# 環境変数チェック
check_env() {
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}エラー: GCP_PROJECT_ID環境変数が設定されていません${NC}"
        echo "export GCP_PROJECT_ID=your-project-id"
        exit 1
    fi

    if [ -z "$SUPABASE_URL" ]; then
        echo -e "${RED}エラー: SUPABASE_URL環境変数が設定されていません${NC}"
        exit 1
    fi

    echo -e "${GREEN}環境変数チェック完了${NC}"
    echo "  - プロジェクトID: $PROJECT_ID"
    echo "  - リージョン: $REGION"
    echo "  - Supabase URL: $SUPABASE_URL"
}

# フロントエンドデプロイ
deploy_frontend() {
    echo -e "${BLUE}=== フロントエンドをデプロイ ===${NC}"

    cd frontend
    gcloud run deploy $FRONTEND_SERVICE \
        --source . \
        --region $REGION \
        --platform managed \
        --allow-unauthenticated \
        --set-env-vars="NEXT_PUBLIC_SUPABASE_URL=$SUPABASE_URL" \
        --set-env-vars="NEXT_PUBLIC_SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY" \
        --set-env-vars="NEXT_PUBLIC_API_URL=https://$BACKEND_SERVICE-$(gcloud run services describe $BACKEND_SERVICE --region $REGION --format 'value(status.url)' 2>/dev/null || echo 'NOT_DEPLOYED_YET')" \
        --memory=512Mi \
        --cpu=1 \
        --timeout=60 \
        --max-instances=10 \
        --project=$PROJECT_ID

    FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE --region $REGION --format 'value(status.url)' --project=$PROJECT_ID)
    echo -e "${GREEN}フロントエンドのデプロイ完了: $FRONTEND_URL${NC}"
    cd ..
}

# バックエンドデプロイ
deploy_backend() {
    echo -e "${BLUE}=== バックエンドをデプロイ ===${NC}"

    cd backend
    gcloud run deploy $BACKEND_SERVICE \
        --source . \
        --region $REGION \
        --platform managed \
        --allow-unauthenticated \
        --set-env-vars="SESSION_TYPE=supabase" \
        --set-env-vars="SUPABASE_URL=$SUPABASE_URL" \
        --set-env-vars="SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY" \
        --set-env-vars="SUPABASE_JWT_SECRET=$SUPABASE_JWT_SECRET" \
        --set-env-vars="STORAGE_MODE=supabase" \
        --set-env-vars="GEMINI_API_KEY=$GEMINI_API_KEY" \
        --set-env-vars="ALLOWED_ORIGINS=*" \
        --memory=1Gi \
        --cpu=1 \
        --timeout=300 \
        --max-instances=10 \
        --project=$PROJECT_ID

    BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --region $REGION --format 'value(status.url)' --project=$PROJECT_ID)
    echo -e "${GREEN}バックエンドのデプロイ完了: $BACKEND_URL${NC}"
    cd ..
}

# ADKデプロイ
deploy_adk() {
    echo -e "${BLUE}=== ADKをデプロイ ===${NC}"

    cd backend
    gcloud run deploy $ADK_SERVICE \
        --source . \
        --region $REGION \
        --platform managed \
        --allow-unauthenticated \
        --set-env-vars="GEMINI_API_KEY=$GEMINI_API_KEY" \
        --command="python,-m,google.adk,dev,--port,8080,--host,0.0.0.0" \
        --memory=512Mi \
        --cpu=1 \
        --timeout=300 \
        --max-instances=5 \
        --project=$PROJECT_ID

    ADK_URL=$(gcloud run services describe $ADK_SERVICE --region $REGION --format 'value(status.url)' --project=$PROJECT_ID)
    echo -e "${GREEN}ADKのデプロイ完了: $ADK_URL${NC}"
    cd ..
}

# メイン処理
main() {
    check_env

    TARGET="${1:-all}"

    case $TARGET in
        frontend)
            deploy_frontend
            ;;
        backend)
            deploy_backend
            ;;
        adk)
            deploy_adk
            ;;
        all)
            deploy_backend  # バックエンドを先にデプロイ
            deploy_frontend
            deploy_adk
            ;;
        *)
            echo -e "${RED}無効なターゲット: $TARGET${NC}"
            echo "使用方法: ./deploy-cloud-run.sh [frontend|backend|adk|all]"
            exit 1
            ;;
    esac

    echo -e "${GREEN}=== デプロイ完了 ===${NC}"
}

main "$@"
