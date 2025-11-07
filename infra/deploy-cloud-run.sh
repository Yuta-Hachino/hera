#!/bin/bash

# ==================================================
# Hera - Cloud Run デプロイスクリプト
# ==================================================

set -e  # エラーが発生したら即座に終了

# ==================================================
# 設定
# ==================================================
PROJECT_ID="${GCP_PROJECT_ID}"
REGION="${GCP_REGION:-asia-northeast1}"
SERVICE_ACCOUNT="${GCP_SERVICE_ACCOUNT}"

# サービス名
BACKEND_SERVICE="hera-backend"
FRONTEND_SERVICE="hera-frontend"
ADK_SERVICE="hera-adk"

# ==================================================
# カラー出力
# ==================================================
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ==================================================
# 前提条件チェック
# ==================================================
check_requirements() {
    log_info "前提条件をチェック中..."

    # gcloud CLI
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI がインストールされていません"
        log_info "https://cloud.google.com/sdk/docs/install からインストールしてください"
        exit 1
    fi

    # プロジェクトID
    if [ -z "$PROJECT_ID" ]; then
        log_error "GCP_PROJECT_ID が設定されていません"
        log_info "環境変数を設定してください: export GCP_PROJECT_ID=your-project-id"
        exit 1
    fi

    # 環境変数ファイル
    if [ ! -f "../.env" ]; then
        log_error ".env ファイルが見つかりません"
        log_info ".env.example をコピーして .env を作成し、必要な環境変数を設定してください"
        exit 1
    fi

    log_success "前提条件チェック完了"
}

# ==================================================
# GCPプロジェクト設定
# ==================================================
setup_gcp_project() {
    log_info "GCPプロジェクトを設定中..."

    # プロジェクトを設定
    gcloud config set project "$PROJECT_ID"

    # 必要なAPIを有効化
    log_info "必要なAPIを有効化中..."
    gcloud services enable \
        run.googleapis.com \
        cloudbuild.googleapis.com \
        artifactregistry.googleapis.com \
        --project="$PROJECT_ID"

    log_success "GCPプロジェクト設定完了"
}

# ==================================================
# 環境変数のロード
# ==================================================
load_env_vars() {
    log_info "環境変数をロード中..."

    # .envファイルから環境変数を読み込み
    if [ -f "../.env" ]; then
        export $(grep -v '^#' ../.env | xargs)
        log_success "環境変数をロードしました"
    else
        log_error ".env ファイルが見つかりません"
        exit 1
    fi
}

# ==================================================
# Backendデプロイ
# ==================================================
deploy_backend() {
    log_info "=== Backend をデプロイ中 ==="

    cd ../backend

    # Firebase Service Account Keyの存在確認
    if [ ! -f "firebase-service-account.json" ]; then
        log_error "firebase-service-account.json が見つかりません"
        log_info "Firebase Console からサービスアカウントキーをダウンロードしてください"
        exit 1
    fi

    # Cloud Runにデプロイ
    gcloud run deploy "$BACKEND_SERVICE" \
        --source . \
        --region="$REGION" \
        --platform=managed \
        --allow-unauthenticated \
        --memory=1Gi \
        --cpu=1 \
        --timeout=300 \
        --max-instances=10 \
        --set-env-vars="GEMINI_API_KEY=${GEMINI_API_KEY}" \
        --set-env-vars="SESSION_TYPE=firebase" \
        --set-env-vars="STORAGE_MODE=firebase" \
        --set-env-vars="FLASK_DEBUG=False" \
        --set-env-vars="PORT=8080" \
        --set-env-vars="ALLOWED_ORIGINS=https://${FRONTEND_SERVICE}-${GCP_REGION}.run.app" \
        --project="$PROJECT_ID"

    # デプロイ後のURLを取得
    BACKEND_URL=$(gcloud run services describe "$BACKEND_SERVICE" \
        --region="$REGION" \
        --format="value(status.url)" \
        --project="$PROJECT_ID")

    cd ../infra

    log_success "Backend デプロイ完了: $BACKEND_URL"
    echo "$BACKEND_URL" > ../.backend_url
}

# ==================================================
# Frontendデプロイ
# ==================================================
deploy_frontend() {
    log_info "=== Frontend をデプロイ中 ==="

    cd ../frontend

    # Backend URLを読み込み
    if [ -f "../.backend_url" ]; then
        BACKEND_URL=$(cat ../.backend_url)
    else
        log_error "Backend URLが見つかりません。先にBackendをデプロイしてください"
        exit 1
    fi

    # Cloud Runにデプロイ
    gcloud run deploy "$FRONTEND_SERVICE" \
        --source . \
        --region="$REGION" \
        --platform=managed \
        --allow-unauthenticated \
        --memory=1Gi \
        --cpu=1 \
        --timeout=60 \
        --max-instances=10 \
        --set-env-vars="NEXT_PUBLIC_API_URL=${BACKEND_URL}" \
        --set-env-vars="NEXT_PUBLIC_FIREBASE_API_KEY=${NEXT_PUBLIC_FIREBASE_API_KEY}" \
        --set-env-vars="NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=${NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN}" \
        --set-env-vars="NEXT_PUBLIC_FIREBASE_PROJECT_ID=${NEXT_PUBLIC_FIREBASE_PROJECT_ID}" \
        --set-env-vars="NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=${NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET}" \
        --set-env-vars="NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=${NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID}" \
        --set-env-vars="NEXT_PUBLIC_FIREBASE_APP_ID=${NEXT_PUBLIC_FIREBASE_APP_ID}" \
        --project="$PROJECT_ID"

    # デプロイ後のURLを取得
    FRONTEND_URL=$(gcloud run services describe "$FRONTEND_SERVICE" \
        --region="$REGION" \
        --format="value(status.url)" \
        --project="$PROJECT_ID")

    cd ../infra

    log_success "Frontend デプロイ完了: $FRONTEND_URL"
    echo "$FRONTEND_URL" > ../.frontend_url
}

# ==================================================
# ADKデプロイ
# ==================================================
deploy_adk() {
    log_info "=== ADK をデプロイ中 ==="

    cd ../backend

    # Cloud Runにデプロイ
    gcloud run deploy "$ADK_SERVICE" \
        --source . \
        --region="$REGION" \
        --platform=managed \
        --allow-unauthenticated \
        --memory=2Gi \
        --cpu=2 \
        --timeout=600 \
        --max-instances=5 \
        --command="python,-m,google.adk,dev,--port,8000,--host,0.0.0.0" \
        --set-env-vars="GEMINI_API_KEY=${GEMINI_API_KEY}" \
        --set-env-vars="SESSION_TYPE=firebase" \
        --set-env-vars="STORAGE_MODE=firebase" \
        --project="$PROJECT_ID"

    # デプロイ後のURLを取得
    ADK_URL=$(gcloud run services describe "$ADK_SERVICE" \
        --region="$REGION" \
        --format="value(status.url)" \
        --project="$PROJECT_ID")

    cd ../infra

    log_success "ADK デプロイ完了: $ADK_URL"
    echo "$ADK_URL" > ../.adk_url
}

# ==================================================
# BackendのALLOWED_ORIGINS更新
# ==================================================
update_cors() {
    log_info "=== CORS設定を更新中 ==="

    FRONTEND_URL=$(cat ../.frontend_url)

    gcloud run services update "$BACKEND_SERVICE" \
        --region="$REGION" \
        --update-env-vars="ALLOWED_ORIGINS=${FRONTEND_URL}" \
        --project="$PROJECT_ID"

    log_success "CORS設定更新完了"
}

# ==================================================
# デプロイサマリー
# ==================================================
show_summary() {
    log_success "========================================="
    log_success "  デプロイ完了！"
    log_success "========================================="

    if [ -f "../.frontend_url" ]; then
        FRONTEND_URL=$(cat ../.frontend_url)
        echo -e "${GREEN}Frontend URL:${NC} $FRONTEND_URL"
    fi

    if [ -f "../.backend_url" ]; then
        BACKEND_URL=$(cat ../.backend_url)
        echo -e "${GREEN}Backend URL:${NC} $BACKEND_URL"
    fi

    if [ -f "../.adk_url" ]; then
        ADK_URL=$(cat ../.adk_url)
        echo -e "${GREEN}ADK URL:${NC} $ADK_URL"
    fi

    echo ""
    log_info "次のステップ:"
    echo "  1. Frontend URLにアクセスしてアプリを確認"
    echo "  2. Firebase Consoleで認証のリダイレクトURIを追加:"
    echo "     ${FRONTEND_URL}/api/auth/callback/google"
    echo ""
}

# ==================================================
# メイン処理
# ==================================================
main() {
    log_info "========================================="
    log_info "  Hera - Cloud Run デプロイ"
    log_info "========================================="
    echo ""

    # 引数チェック
    if [ "$#" -eq 0 ]; then
        log_error "引数を指定してください"
        echo ""
        echo "使い方:"
        echo "  $0 all              # 全サービスをデプロイ"
        echo "  $0 backend          # Backendのみデプロイ"
        echo "  $0 frontend         # Frontendのみデプロイ"
        echo "  $0 adk              # ADKのみデプロイ"
        echo "  $0 setup            # GCPプロジェクトのセットアップのみ"
        exit 1
    fi

    # 前提条件チェック
    check_requirements

    # 環境変数ロード
    load_env_vars

    # コマンド実行
    case "$1" in
        setup)
            setup_gcp_project
            ;;
        backend)
            deploy_backend
            ;;
        frontend)
            deploy_frontend
            ;;
        adk)
            deploy_adk
            ;;
        all)
            setup_gcp_project
            deploy_backend
            deploy_frontend
            deploy_adk
            update_cors
            show_summary
            ;;
        *)
            log_error "不明なコマンド: $1"
            exit 1
            ;;
    esac

    log_success "完了しました！"
}

# スクリプト実行
main "$@"
