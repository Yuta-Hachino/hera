#!/bin/bash

# ==================================================
# Hera - Automated Deployment Script
# ==================================================
# このスクリプトはGCP Cloud Runへの完全な自動デプロイを実行します

set -e  # エラーが発生したら即座に終了

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ==================================================
# Step 0: 環境設定の読み込み
# ==================================================

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 0: 環境設定の読み込み${NC}"
echo -e "${BLUE}========================================${NC}"

# terraform.tfvarsから設定を読み込む
TFVARS_FILE="terraform/environments/prod/terraform.tfvars"

if [ ! -f "$TFVARS_FILE" ]; then
    echo -e "${RED}❌ エラー: $TFVARS_FILE が見つかりません${NC}"
    exit 1
fi

# プロジェクトID、リージョン、環境を抽出
PROJECT_ID=$(grep 'project_id' "$TFVARS_FILE" | cut -d '"' -f 2)
REGION=$(grep 'region' "$TFVARS_FILE" | cut -d '"' -f 2)
ENVIRONMENT=$(grep 'environment' "$TFVARS_FILE" | cut -d '"' -f 2)

echo -e "${GREEN}✓ プロジェクトID: $PROJECT_ID${NC}"
echo -e "${GREEN}✓ リージョン: $REGION${NC}"
echo -e "${GREEN}✓ 環境: $ENVIRONMENT${NC}"
echo ""

# ==================================================
# Step 1: gcloud設定の確認
# ==================================================

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 1: gcloud設定の確認${NC}"
echo -e "${BLUE}========================================${NC}"

# gcloudがインストールされているか確認
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ エラー: gcloud CLIがインストールされていません${NC}"
    echo -e "${YELLOW}https://cloud.google.com/sdk/docs/install からインストールしてください${NC}"
    exit 1
fi

# 現在のプロジェクト設定を確認
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
echo -e "${YELLOW}現在のgcloudプロジェクト: $CURRENT_PROJECT${NC}"

if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
    echo -e "${YELLOW}⚠ プロジェクトを $PROJECT_ID に切り替えます${NC}"
    gcloud config set project "$PROJECT_ID"
fi

# 認証確認
echo -e "${YELLOW}認証状態を確認中...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "."; then
    echo -e "${RED}❌ エラー: gcloudにログインしていません${NC}"
    echo -e "${YELLOW}以下のコマンドでログインしてください:${NC}"
    echo -e "${YELLOW}gcloud auth login${NC}"
    exit 1
fi

echo -e "${GREEN}✓ gcloud設定完了${NC}"
echo ""

# ==================================================
# Step 2: Docker認証
# ==================================================

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 2: Docker認証${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "${YELLOW}Artifact Registryへの認証を設定中...${NC}"
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

echo -e "${GREEN}✓ Docker認証完了${NC}"
echo ""

# ==================================================
# Step 3: Artifact Registry リポジトリの作成
# ==================================================

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 3: Artifact Registry リポジトリの作成${NC}"
echo -e "${BLUE}========================================${NC}"

REPO_NAME="hera"

# リポジトリが存在するか確認
if gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" &>/dev/null; then
    echo -e "${YELLOW}⚠ リポジトリ '$REPO_NAME' は既に存在します${NC}"
else
    echo -e "${YELLOW}リポジトリ '$REPO_NAME' を作成中...${NC}"
    gcloud artifacts repositories create "$REPO_NAME" \
        --repository-format=docker \
        --location="$REGION" \
        --description="Hera application Docker images"
    echo -e "${GREEN}✓ リポジトリ作成完了${NC}"
fi
echo ""

# ==================================================
# Step 4: Backend Dockerイメージのビルド＆プッシュ
# ==================================================

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 4: Backend Dockerイメージのビルド＆プッシュ${NC}"
echo -e "${BLUE}========================================${NC}"

cd ../backend

BACKEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/hera-backend:latest"

echo -e "${YELLOW}Backendイメージをビルド中...${NC}"
docker build -t "$BACKEND_IMAGE" -f Dockerfile.cloud-run .

echo -e "${YELLOW}Backendイメージをプッシュ中...${NC}"
docker push "$BACKEND_IMAGE"

echo -e "${GREEN}✓ Backend デプロイ完了${NC}"
echo -e "${GREEN}  イメージ: $BACKEND_IMAGE${NC}"

cd ../infra
echo ""

# ==================================================
# Step 5: Frontend Dockerイメージのビルド＆プッシュ
# ==================================================

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 5: Frontend Dockerイメージのビルド＆プッシュ${NC}"
echo -e "${BLUE}========================================${NC}"

cd ../frontend

FRONTEND_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/hera-frontend:latest"

echo -e "${YELLOW}Frontendイメージをビルド中...${NC}"
docker build -t "$FRONTEND_IMAGE" -f Dockerfile.cloud-run .

echo -e "${YELLOW}Frontendイメージをプッシュ中...${NC}"
docker push "$FRONTEND_IMAGE"

echo -e "${GREEN}✓ Frontend デプロイ完了${NC}"
echo -e "${GREEN}  イメージ: $FRONTEND_IMAGE${NC}"

cd ../infra
echo ""

# ==================================================
# Step 6: ADK Dockerイメージのビルド＆プッシュ (オプション)
# ==================================================

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 6: ADK Dockerイメージのビルド＆プッシュ${NC}"
echo -e "${BLUE}========================================${NC}"

if [ -d "../adk" ] && [ -f "../adk/Dockerfile" ]; then
    cd ../adk

    ADK_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/hera-adk:latest"

    echo -e "${YELLOW}ADKイメージをビルド中...${NC}"
    docker build -t "$ADK_IMAGE" -f Dockerfile .

    echo -e "${YELLOW}ADKイメージをプッシュ中...${NC}"
    docker push "$ADK_IMAGE"

    echo -e "${GREEN}✓ ADK デプロイ完了${NC}"
    echo -e "${GREEN}  イメージ: $ADK_IMAGE${NC}"

    cd ../infra
else
    echo -e "${YELLOW}⚠ ADKディレクトリが見つからないため、スキップします${NC}"
fi
echo ""

# ==================================================
# Step 7: Terraformでインフラをデプロイ
# ==================================================

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 7: Terraformでインフラをデプロイ${NC}"
echo -e "${BLUE}========================================${NC}"

cd terraform

# Terraform初期化
if [ ! -d ".terraform" ]; then
    echo -e "${YELLOW}Terraformを初期化中...${NC}"
    terraform init
    echo -e "${GREEN}✓ Terraform初期化完了${NC}"
else
    echo -e "${YELLOW}⚠ Terraformは既に初期化されています${NC}"
fi
echo ""

# Terraform plan
echo -e "${YELLOW}Terraform planを実行中...${NC}"
terraform plan -var-file=environments/prod/terraform.tfvars -out=terraform.tfplan
echo ""

# ユーザーに確認
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}上記の変更内容を確認してください${NC}"
echo -e "${YELLOW}========================================${NC}"
read -p "デプロイを続行しますか？ (yes/no): " CONTINUE

if [ "$CONTINUE" != "yes" ]; then
    echo -e "${RED}❌ デプロイをキャンセルしました${NC}"
    exit 0
fi
echo ""

# Terraform apply
echo -e "${YELLOW}Terraform applyを実行中...${NC}"
terraform apply terraform.tfplan

echo -e "${GREEN}✓ Terraformデプロイ完了${NC}"
echo ""

cd ..

# ==================================================
# Step 8: デプロイ結果の確認
# ==================================================

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 8: デプロイ結果の確認${NC}"
echo -e "${BLUE}========================================${NC}"

cd terraform

# Terraform outputから結果を取得
echo -e "${YELLOW}デプロイされたURLを取得中...${NC}"
BACKEND_URL=$(terraform output -raw backend_url 2>/dev/null || echo "取得失敗")
FRONTEND_URL=$(terraform output -raw frontend_url 2>/dev/null || echo "取得失敗")
ADK_URL=$(terraform output -raw adk_url 2>/dev/null || echo "取得失敗")

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}デプロイ完了！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${GREEN}Frontend URL: ${FRONTEND_URL}${NC}"
echo -e "${GREEN}Backend URL:  ${BACKEND_URL}${NC}"
echo -e "${GREEN}ADK URL:      ${ADK_URL}${NC}"
echo ""

# URLをファイルに保存
echo "$BACKEND_URL" > ../../.backend_url
echo "$FRONTEND_URL" > ../../.frontend_url

echo -e "${BLUE}次のステップ:${NC}"
echo -e "1. Frontend URLにアクセスしてアプリを確認"
echo -e "2. Firebase Consoleで認証のリダイレクトURIを追加:"
echo -e "   ${YELLOW}https://console.firebase.google.com/project/test-6554c/authentication/providers${NC}"
echo -e "   - 承認済みドメインに追加: ${FRONTEND_URL}"
echo ""

# カスタムドメインが有効な場合
CUSTOM_DOMAIN_ENABLED=$(terraform output -raw custom_domain_enabled 2>/dev/null || echo "false")
if [ "$CUSTOM_DOMAIN_ENABLED" = "true" ]; then
    echo -e "${BLUE}カスタムドメインDNS設定:${NC}"
    terraform output -json dns_records | jq -r 'to_entries[] | "  \(.key): \(.value.name) CNAME \(.value.value)"'
    echo ""
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}デプロイスクリプト完了${NC}"
echo -e "${GREEN}========================================${NC}"
