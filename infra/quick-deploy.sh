#!/bin/bash

# ==================================================
# Hera - ワンコマンドデプロイスクリプト
# ==================================================
# サービスアカウントセットアップ + デプロイを一気に実行

set -e

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ID="gen-lang-client-0830629645"
SA_NAME="hera-deploy"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
KEY_FILE="$(dirname "$0")/gcp-deploy-key.json"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Hera ワンコマンドデプロイ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# サービスアカウントキーが既にあるか確認
if [ -f "$KEY_FILE" ]; then
    echo -e "${GREEN}✓ サービスアカウントキーが既に存在します${NC}"
    echo ""
    read -p "既存のキーを使用しますか？ (yes/no): " USE_EXISTING
    if [ "$USE_EXISTING" = "yes" ]; then
        echo -e "${GREEN}既存のキーでデプロイを開始します${NC}"
        echo ""
        # デプロイスクリプトを実行
        exec "$(dirname "$0")/auto-deploy.sh"
        exit 0
    fi
fi

echo -e "${YELLOW}サービスアカウントのセットアップが必要です${NC}"
echo ""

# Docker起動確認
echo -e "${YELLOW}Dockerデーモンを確認中...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ エラー: Dockerが起動していません${NC}"
    echo -e "${YELLOW}Docker Desktopを起動してから再実行してください${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker起動確認完了${NC}"
echo ""

# gcloud認証確認
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Google Cloud 認証が必要です${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo -e "以下のコマンドをコピペして実行してください："
echo ""
echo -e "${BLUE}# 1. Google Cloud にログイン${NC}"
echo "gcloud auth login"
echo ""
echo -e "${BLUE}# 2. プロジェクトを設定${NC}"
echo "gcloud config set project $PROJECT_ID"
echo ""
echo -e "${BLUE}# 3. サービスアカウントを作成（既存の場合はスキップ）${NC}"
echo "gcloud iam service-accounts create $SA_NAME --display-name='Hera Deploy Service Account' --project=$PROJECT_ID 2>/dev/null || echo 'サービスアカウントは既に存在します'"
echo ""
echo -e "${BLUE}# 4. IAM権限を付与${NC}"
echo "for ROLE in roles/run.admin roles/iam.serviceAccountUser roles/storage.admin roles/artifactregistry.admin roles/secretmanager.admin roles/cloudbuild.builds.editor roles/iam.securityAdmin; do gcloud projects add-iam-policy-binding $PROJECT_ID --member='serviceAccount:$SA_EMAIL' --role=\$ROLE --quiet > /dev/null 2>&1; done && echo '✓ IAM権限付与完了'"
echo ""
echo -e "${BLUE}# 5. サービスアカウントキーを作成${NC}"
echo "gcloud iam service-accounts keys create $KEY_FILE --iam-account=$SA_EMAIL --project=$PROJECT_ID"
echo ""
echo -e "${YELLOW}========================================${NC}"
echo ""

read -p "上記のコマンドを実行しましたか？ (yes/no): " COMPLETED

if [ "$COMPLETED" != "yes" ]; then
    echo -e "${RED}セットアップをキャンセルしました${NC}"
    echo -e "${YELLOW}コマンドを実行後、再度このスクリプトを実行してください${NC}"
    exit 0
fi

# サービスアカウントキーの存在確認
if [ ! -f "$KEY_FILE" ]; then
    echo -e "${RED}❌ エラー: サービスアカウントキーが見つかりません${NC}"
    echo -e "${YELLOW}キーファイルの作成を確認してください: $KEY_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✓ サービスアカウントキー確認完了${NC}"
echo ""

# デプロイ開始
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}デプロイを開始します${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# auto-deploy.sh を実行
exec "$(dirname "$0")/auto-deploy.sh"
