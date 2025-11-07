#!/bin/bash
set -e

echo '========================================'
echo 'Hera自動デプロイ開始'
echo '========================================'

# サービスアカウントキーの確認
if [ -f '/workspace/infra/gcp-deploy-key.json' ]; then
  echo '✓ サービスアカウントキーが見つかりました'
  export GOOGLE_APPLICATION_CREDENTIALS='/workspace/infra/gcp-deploy-key.json'
  gcloud auth activate-service-account --key-file=/workspace/infra/gcp-deploy-key.json
else
  echo '❌ エラー: gcp-deploy-key.json が見つかりません'
  echo '詳細は SERVICE_ACCOUNT_SETUP.md を参照してください'
  exit 1
fi

# 必要なツールのインストール
echo 'Installing required tools...'
apt-get update -qq
apt-get install -y -qq docker.io jq > /dev/null 2>&1

# Terraform のインストール
echo 'Installing Terraform...'
apt-get install -y -qq wget unzip > /dev/null 2>&1
wget -q https://releases.hashicorp.com/terraform/1.6.6/terraform_1.6.6_linux_amd64.zip
unzip -q terraform_1.6.6_linux_amd64.zip
mv terraform /usr/local/bin/
rm terraform_1.6.6_linux_amd64.zip

# gcloud設定確認
echo '========================================'
echo 'Step 1: gcloud設定確認'
echo '========================================'
gcloud config set project gen-lang-client-0830629645
gcloud config set compute/region asia-northeast1
echo "Project: $(gcloud config get-value project)"
echo "Region: $(gcloud config get-value compute/region)"
echo ''

# Docker認証
echo '========================================'
echo 'Step 2: Docker認証'
echo '========================================'
gcloud auth configure-docker asia-northeast1-docker.pkg.dev --quiet
echo '✓ Docker認証完了'
echo ''

# Artifact Registry リポジトリ作成
echo '========================================'
echo 'Step 3: Artifact Registryリポジトリ作成'
echo '========================================'
if gcloud artifacts repositories describe hera --location=asia-northeast1 > /dev/null 2>&1; then
  echo '⚠ リポジトリ hera は既に存在します'
else
  gcloud artifacts repositories create hera \
    --repository-format=docker \
    --location=asia-northeast1 \
    --description='Hera application Docker images'
  echo '✓ リポジトリ作成完了'
fi
echo ''

# Backend Dockerイメージのビルド＆プッシュ
echo '========================================'
echo 'Step 4: Backend Dockerイメージビルド＆プッシュ'
echo '========================================'
cd /workspace/backend
docker build -t asia-northeast1-docker.pkg.dev/gen-lang-client-0830629645/hera/hera-backend:latest -f Dockerfile .
docker push asia-northeast1-docker.pkg.dev/gen-lang-client-0830629645/hera/hera-backend:latest
echo '✓ Backend イメージプッシュ完了'
echo ''

# Terraform Phase 1: Backendのみデプロイ
echo '========================================'
echo 'Step 5: Terraform Phase 1 - Backendデプロイ'
echo '========================================'
cd /workspace/infra/terraform

terraform init
echo '✓ Terraform初期化完了'
echo ''

# Backend専用のターゲットでデプロイ
terraform apply -var-file=environments/prod/terraform.tfvars -target=module.backend -target=google_service_account.cloud_run -target=module.secret_gemini_api_key -target=module.secret_firebase_api_key -target=random_id.suffix -auto-approve
echo '✓ Backendデプロイ完了'
echo ''

# Cloud Run Backendサービスを強制的に最新イメージで更新
echo '========================================'
echo 'Step 5.5: Backend強制更新（最新イメージ適用）'
echo '========================================'
gcloud run services update hera-backend-prod \
  --image=asia-northeast1-docker.pkg.dev/gen-lang-client-0830629645/hera/hera-backend:latest \
  --region=asia-northeast1 \
  --quiet
echo '✓ Backend強制更新完了'
echo ''

# BackendのURLを取得
BACKEND_URL=$(terraform output -raw backend_url 2>/dev/null)
echo "Backend URL: $BACKEND_URL"
echo ''

# Frontend Dockerイメージのビルド＆プッシュ
echo '========================================'
echo 'Step 6: Frontend Dockerイメージビルド＆プッシュ（Backend URL使用）'
echo '========================================'
cd /workspace/frontend

# Firebase設定を環境変数から読み込む
FIREBASE_API_KEY=${FIREBASE_API_KEY:-"AIzaSyDP2oDcOunRfIYfh3GPvyQGw8LFQW7qp3E"}
FIREBASE_AUTH_DOMAIN=${FIREBASE_AUTH_DOMAIN:-"test-6554c.firebaseapp.com"}
FIREBASE_PROJECT_ID=${FIREBASE_PROJECT_ID:-"test-6554c"}
FIREBASE_STORAGE_BUCKET=${FIREBASE_STORAGE_BUCKET:-"test-6554c.firebasestorage.app"}
FIREBASE_MESSAGING_SENDER_ID=${FIREBASE_MESSAGING_SENDER_ID:-"716580137550"}
FIREBASE_APP_ID=${FIREBASE_APP_ID:-"1:716580137550:web:754d37c7f4f51b3363b11f"}

# ビルド引数としてBackend URLとFirebase設定を渡してDockerイメージをビルド
docker build \
  --build-arg NEXT_PUBLIC_API_URL="$BACKEND_URL" \
  --build-arg NEXT_PUBLIC_FIREBASE_API_KEY="$FIREBASE_API_KEY" \
  --build-arg NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN="$FIREBASE_AUTH_DOMAIN" \
  --build-arg NEXT_PUBLIC_FIREBASE_PROJECT_ID="$FIREBASE_PROJECT_ID" \
  --build-arg NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET="$FIREBASE_STORAGE_BUCKET" \
  --build-arg NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID="$FIREBASE_MESSAGING_SENDER_ID" \
  --build-arg NEXT_PUBLIC_FIREBASE_APP_ID="$FIREBASE_APP_ID" \
  -t asia-northeast1-docker.pkg.dev/gen-lang-client-0830629645/hera/hera-frontend:latest \
  -f Dockerfile .

docker push asia-northeast1-docker.pkg.dev/gen-lang-client-0830629645/hera/hera-frontend:latest
echo '✓ Frontend イメージプッシュ完了'
echo ''

# Terraform Phase 2: Frontendデプロイ
echo '========================================'
echo 'Step 7: Terraform Phase 2 - Frontendデプロイ'
echo '========================================'
cd /workspace/infra/terraform

terraform apply -var-file=environments/prod/terraform.tfvars -auto-approve
echo '✓ Terraform全体デプロイ完了'
echo ''

# Cloud Run Frontendサービスを強制的に最新イメージで更新
echo '========================================'
echo 'Step 7.5: Frontend強制更新（最新イメージ適用）'
echo '========================================'
gcloud run services update hera-frontend-prod \
  --image=asia-northeast1-docker.pkg.dev/gen-lang-client-0830629645/hera/hera-frontend:latest \
  --region=asia-northeast1 \
  --quiet
echo '✓ Frontend強制更新完了'
echo ''

# Frontend URLを取得
FRONTEND_URL=$(terraform output -raw frontend_url 2>/dev/null)
echo "Frontend URL: $FRONTEND_URL"
echo ''

# Backend ALLOWED_ORIGINSを正しいFrontend URLで更新
echo '========================================'
echo 'Step 7.75: Backend CORS設定更新'
echo '========================================'
gcloud run services update hera-backend-prod \
  --update-env-vars ALLOWED_ORIGINS="$FRONTEND_URL" \
  --region=asia-northeast1 \
  --quiet
echo '✓ Backend CORS設定更新完了'
echo ''

# デプロイ結果の確認
echo '========================================'
echo 'Step 8: デプロイ結果確認'
echo '========================================'
BACKEND_URL=$(terraform output -raw backend_url 2>/dev/null || echo '取得失敗')
FRONTEND_URL=$(terraform output -raw frontend_url 2>/dev/null || echo '取得失敗')

echo ''
echo '========================================'
echo 'デプロイ完了！'
echo '========================================'
echo ''
echo "Frontend URL: $FRONTEND_URL"
echo "Backend URL: $BACKEND_URL"
echo ''

# URLをファイルに保存
echo "$BACKEND_URL" > /workspace/.backend_url
echo "$FRONTEND_URL" > /workspace/.frontend_url

echo '次のステップ:'
echo '1. Frontend URLにアクセスしてアプリを確認'
echo '2. Firebase Consoleで認証のリダイレクトURIを追加:'
echo '   https://console.firebase.google.com/project/test-6554c/authentication/providers'
echo "   - 承認済みドメインに追加: $FRONTEND_URL"
echo ''
echo '========================================'
echo 'デプロイスクリプト完了'
echo '========================================'
