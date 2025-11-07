#!/bin/bash

# ==================================================
# Hera - 完全自動デプロイスクリプト（Docker版）
# ==================================================
# Google Cloud SDK Dockerコンテナ内で全自動デプロイを実行

set -e

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Hera 完全自動デプロイ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# サービスアカウントキー確認
echo -e "${YELLOW}サービスアカウントキーを確認中...${NC}"
if [ ! -f "$(dirname "$0")/gcp-deploy-key.json" ]; then
    echo -e "${RED}❌ エラー: gcp-deploy-key.json が見つかりません${NC}"
    echo -e "${YELLOW}サービスアカウントキーを作成してください:${NC}"
    echo -e "${YELLOW}  詳細は SERVICE_ACCOUNT_SETUP.md を参照${NC}"
    echo ""
    echo -e "${YELLOW}または、gcloud認証を使用する場合は以下を実行:${NC}"
    echo -e "${YELLOW}  gcloud auth login${NC}"
    echo -e "${YELLOW}  gcloud auth application-default login${NC}"
    exit 1
fi
echo -e "${GREEN}✓ サービスアカウントキー確認完了${NC}"
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

# デプロイ開始確認
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}以下の設定でデプロイを開始します:${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "  プロジェクトID: ${GREEN}gen-lang-client-0830629645${NC}"
echo -e "  リージョン: ${GREEN}asia-northeast1${NC}"
echo -e "  環境: ${GREEN}prod${NC}"
echo ""
echo -e "${YELLOW}デプロイには15-20分程度かかります${NC}"
echo ""

read -p "続行しますか？ (yes/no): " CONTINUE
if [ "$CONTINUE" != "yes" ]; then
    echo -e "${RED}❌ デプロイをキャンセルしました${NC}"
    exit 0
fi
echo ""

# Docker Composeでデプロイ実行
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Docker コンテナ内でデプロイを実行中...${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

cd "$(dirname "$0")"

docker-compose -f docker-compose.deploy.yml up --abort-on-container-exit

# 結果確認
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ デプロイが正常に完了しました！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""

    # URLファイルが存在すれば表示
    if [ -f "../.frontend_url" ]; then
        FRONTEND_URL=$(cat ../.frontend_url)
        echo -e "${GREEN}Frontend URL: ${FRONTEND_URL}${NC}"
    fi

    if [ -f "../.backend_url" ]; then
        BACKEND_URL=$(cat ../.backend_url)
        echo -e "${GREEN}Backend URL: ${BACKEND_URL}${NC}"
    fi

    echo ""
    echo -e "${BLUE}次のステップ:${NC}"
    echo -e "1. Firebase Consoleで認証設定を更新"
    echo -e "   ${YELLOW}https://console.firebase.google.com/project/test-6554c/authentication/providers${NC}"
    echo -e "2. Frontend URLにアクセスしてアプリを確認"
    echo ""
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}❌ デプロイ中にエラーが発生しました${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo -e "${YELLOW}ログを確認してエラーを修正してください${NC}"
    exit 1
fi

# コンテナをクリーンアップ
echo -e "${YELLOW}コンテナをクリーンアップ中...${NC}"
docker-compose -f docker-compose.deploy.yml down > /dev/null 2>&1
echo -e "${GREEN}✓ クリーンアップ完了${NC}"
