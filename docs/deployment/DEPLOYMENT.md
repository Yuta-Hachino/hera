# デプロイメントガイド

このドキュメントでは、Heraアプリケーションをローカル環境（Docker）とCloud Runにデプロイする方法を説明します。

## 目次

1. [ローカル環境（Docker）でのデプロイ](#ローカル環境dockerでのデプロイ)
2. [Cloud Runへのデプロイ](#cloud-runへのデプロイ)
3. [環境変数の設定](#環境変数の設定)

---

## ローカル環境（Docker）でのデプロイ

### 前提条件

- Docker & Docker Composeがインストールされていること
- Firebase プロジェクトが作成されていること
- Firebase Admin SDK サービスアカウントキーが取得済みであること

### 手順

**1. 環境変数ファイルを作成**

\`\`\`bash
# プロジェクトルートで.envファイルを作成
cp .env.example .env
\`\`\`

`.env`ファイルを編集して、実際の値を設定してください。

**2. Firebase サービスアカウントキーを配置**

\`\`\`bash
# Firebase Consoleからダウンロードしたサービスアカウントキーを配置
cp /path/to/your/service-account-key.json backend/service-account-key.json
\`\`\`

**3. Dockerコンテナを起動**

\`\`\`bash
# すべてのサービスをビルドして起動
docker-compose up --build

# またはバックグラウンドで起動
docker-compose up --build -d
\`\`\`

**4. アプリケーションにアクセス**

- フロントエンド: http://localhost:3000
- バックエンドAPI: http://localhost:8080
- ADK開発UI: http://localhost:8000

**5. ログの確認**

\`\`\`bash
# すべてのサービスのログを表示
docker-compose logs -f

# 特定のサービスのログを表示
docker-compose logs -f backend
\`\`\`

**6. コンテナの停止**

\`\`\`bash
docker-compose down
\`\`\`

---

## Cloud Runへのデプロイ

### 前提条件

- Google Cloud SDKがインストールされていること
- GCPプロジェクトが作成され、billing が有効化されていること

### デプロイ手順

**1. GCP認証とプロジェクト設定**

\`\`\`bash
gcloud auth login
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID
export REGION="asia-northeast1"
\`\`\`

**2. 必要なAPIを有効化**

\`\`\`bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
\`\`\`

**3. Secret Managerにシークレットを登録**

\`\`\`bash
# Gemini APIキー
echo -n "your-gemini-api-key" | gcloud secrets create gemini-api-key --data-file=-

# Firebase サービスアカウントキー
gcloud secrets create firebase-service-account-key --data-file=backend/service-account-key.json
\`\`\`

**4. バックエンドをデプロイ**

\`\`\`bash
cd backend
gcloud run deploy hera-backend \
    --source . \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID" \
    --set-secrets="GEMINI_API_KEY=gemini-api-key:latest"
\`\`\`

**5. フロントエンドをデプロイ**

\`\`\`bash
cd ../frontend
BACKEND_URL=$(gcloud run services describe hera-backend --region $REGION --format 'value(status.url)')

gcloud run deploy hera-frontend \
    --source . \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="NEXT_PUBLIC_API_URL=$BACKEND_URL"
\`\`\`

詳細は、プロジェクト内のドキュメントを参照してください。
