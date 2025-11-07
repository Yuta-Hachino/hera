#!/bin/bash

# ==================================================
# サービスアカウント自動セットアップスクリプト
# ==================================================

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
echo -e "${BLUE}サービスアカウントセットアップ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# gcloud CLIインストール確認
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ エラー: gcloud CLIがインストールされていません${NC}"
    echo -e "${YELLOW}https://cloud.google.com/sdk/docs/install からインストールしてください${NC}"
    exit 1
fi

# プロジェクト設定
echo -e "${YELLOW}プロジェクトを設定中...${NC}"
gcloud config set project "$PROJECT_ID"
echo -e "${GREEN}✓ プロジェクト設定完了${NC}"
echo ""

# サービスアカウント存在確認
echo -e "${YELLOW}サービスアカウントを確認中...${NC}"
if gcloud iam service-accounts describe "$SA_EMAIL" --project="$PROJECT_ID" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ サービスアカウント '$SA_NAME' は既に存在します${NC}"
else
    echo -e "${YELLOW}サービスアカウントを作成中...${NC}"
    gcloud iam service-accounts create "$SA_NAME" \
        --display-name="Hera Deploy Service Account" \
        --project="$PROJECT_ID"
    echo -e "${GREEN}✓ サービスアカウント作成完了${NC}"
fi
echo ""

# IAM権限付与
echo -e "${YELLOW}IAM権限を付与中...${NC}"

ROLES=(
    "roles/run.admin"
    "roles/iam.serviceAccountUser"
    "roles/storage.admin"
    "roles/artifactregistry.admin"
    "roles/secretmanager.admin"
    "roles/cloudbuild.builds.editor"
    "roles/iam.securityAdmin"
)

for ROLE in "${ROLES[@]}"; do
    echo -e "${YELLOW}  - $ROLE を付与中...${NC}"
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="$ROLE" \
        --quiet > /dev/null 2>&1
done

echo -e "${GREEN}✓ IAM権限付与完了${NC}"
echo ""

# サービスアカウントキーの作成
echo -e "${YELLOW}サービスアカウントキーを作成中...${NC}"

if [ -f "$KEY_FILE" ]; then
    echo -e "${YELLOW}⚠ 既存のキーファイルが見つかりました${NC}"
    read -p "上書きしますか？ (yes/no): " OVERWRITE
    if [ "$OVERWRITE" != "yes" ]; then
        echo -e "${YELLOW}キーファイルの作成をスキップしました${NC}"
        exit 0
    fi
    rm "$KEY_FILE"
fi

gcloud iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$SA_EMAIL" \
    --project="$PROJECT_ID"

echo -e "${GREEN}✓ サービスアカウントキー作成完了${NC}"
echo ""

# 確認
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}セットアップ完了！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}サービスアカウント:${NC} $SA_EMAIL"
echo -e "${GREEN}キーファイル:${NC} $KEY_FILE"
echo ""
echo -e "${YELLOW}次のステップ:${NC}"
echo -e "  cd /Users/user/dev/hera/infra"
echo -e "  ./auto-deploy.sh"
echo ""
echo -e "${RED}⚠ 重要:${NC}"
echo -e "  - キーファイルは機密情報です"
echo -e "  - Gitにコミットしないでください（.gitignoreに追加済み）"
echo -e "  - 定期的にキーをローテーションしてください"
echo ""
