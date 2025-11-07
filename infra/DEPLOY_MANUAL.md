# Hera - Cloud Run デプロイマニュアル

Firebase + Cloud Run 構成でHeraアプリをデプロイする手順です。

## 📋 目次

1. [前提条件](#前提条件)
2. [準備 (初回のみ)](#準備-初回のみ)
3. [デプロイ実行](#デプロイ実行)
4. [デプロイ後の設定](#デプロイ後の設定)
5. [トラブルシューティング](#トラブルシューティング)

---

## 前提条件

以下がインストール済みであることを確認してください:

- ✅ [Google Cloud SDK (gcloud CLI)](https://cloud.google.com/sdk/docs/install)
- ✅ [Node.js 18以上](https://nodejs.org/)
- ✅ [Python 3.11以上](https://www.python.org/)
- ✅ [Docker](https://www.docker.com/)

---

## 準備 (初回のみ)

### Step 1: Google Cloud プロジェクト作成

```bash
# Google Cloudにログイン
gcloud auth login

# プロジェクトを作成 (プロジェクトIDは一意である必要があります)
gcloud projects create hera-production-YOUR_SUFFIX --name="Hera Production"

# プロジェクトIDを環境変数にエクスポート
export GCP_PROJECT_ID=hera-production-YOUR_SUFFIX
export GCP_REGION=asia-northeast1
```

### Step 2: Firebase プロジェクト設定

1. [Firebase Console](https://console.firebase.google.com/) にアクセス
2. 「プロジェクトを追加」をクリック
3. 先ほど作成したGCPプロジェクト (`hera-production-YOUR_SUFFIX`) を選択
4. Firebaseプロジェクトとして有効化

### Step 3: Firebase Service Account Key 取得

1. Firebase Console > ⚙️設定 > サービスアカウント
2. 「新しい秘密鍵の生成」をクリック
3. JSONファイルをダウンロード
4. `backend/firebase-service-account.json` として保存:
   ```bash
   mv ~/Downloads/hera-production-*.json backend/firebase-service-account.json
   ```

### Step 4: Firestore Database 有効化

1. Firebase Console > ビルド > Firestore Database
2. 「データベースを作成」をクリック
3. ロケーション: `asia-northeast1` (Tokyo)
4. セキュリティルール: 本番モードで開始

### Step 5: Firebase Authentication 設定

1. Firebase Console > ビルド > Authentication
2. 「始める」をクリック
3. Google プロバイダを有効化:
   - サポートメール: あなたのメールアドレス
   - プロジェクトの公開名: Hera
4. 「保存」をクリック

### Step 6: Firebase Storage 設定

1. Firebase Console > ビルド > Storage
2. 「始める」をクリック
3. ロケーション: `asia-northeast1` (Tokyo)
4. セキュリティルール: 本番モードで開始

### Step 7: 環境変数ファイル作成

```bash
# プロジェクトルートに .env ファイルを作成
cp .env.example .env
```

`.env` ファイルを編集:

```bash
# GCP設定
GCP_PROJECT_ID=hera-production-YOUR_SUFFIX
GCP_REGION=asia-northeast1

# Gemini API
GEMINI_API_KEY=your-gemini-api-key  # https://aistudio.google.com/app/apikey

# Firebase設定 (Firebase Console > ⚙️設定 > 全般 から取得)
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
NEXT_PUBLIC_FIREBASE_APP_ID=your-app-id
```

---

## デプロイ実行

### 初回デプロイ (全サービス)

```bash
# 環境変数をエクスポート
export GCP_PROJECT_ID=hera-production-YOUR_SUFFIX
export GCP_REGION=asia-northeast1

# 全サービスをデプロイ (infraディレクトリから実行)
cd infra
./deploy-cloud-run.sh all
```

デプロイには **15-20分** かかります。

### 個別デプロイ

```bash
# infraディレクトリから実行
cd infra

# Backendのみ
./deploy-cloud-run.sh backend

# Frontendのみ
./deploy-cloud-run.sh frontend

# ADKのみ
./deploy-cloud-run.sh adk
```

---

## デプロイ後の設定

### Step 1: Firebase Authentication の承認済みドメイン追加

デプロイ完了後に表示されたFrontend URLをコピーして:

1. Firebase Console > Authentication > Settings
2. 「承認済みドメイン」タブ
3. 「ドメインを追加」をクリック
4. デプロイされたFrontend URLのドメイン部分を追加:
   ```
   hera-frontend-xxxx-uc.a.run.app
   ```

### Step 2: アプリにアクセス

```
https://hera-frontend-xxxx-uc.a.run.app
```

---

## トラブルシューティング

### エラー: `firebase-service-account.json が見つかりません`

**原因**: Firebase Service Account Keyが配置されていない

**解決方法**:
```bash
# Step 3 を参照して、firebase-service-account.json をダウンロード
mv ~/Downloads/hera-production-*.json backend/firebase-service-account.json
```

### エラー: `GCP_PROJECT_ID が設定されていません`

**原因**: 環境変数が設定されていない

**解決方法**:
```bash
export GCP_PROJECT_ID=hera-production-YOUR_SUFFIX
export GCP_REGION=asia-northeast1
```

### エラー: Cloud Runデプロイ時に `permission denied`

**原因**: GCPプロジェクトの課金が有効化されていない、または必要な権限がない

**解決方法**:
```bash
# 課金アカウントを確認
gcloud billing accounts list

# 課金アカウントをプロジェクトにリンク
gcloud billing projects link $GCP_PROJECT_ID \
  --billing-account=BILLING_ACCOUNT_ID
```

### Firebase Authentication が動作しない

**原因**: 承認済みドメインが追加されていない

**解決方法**:
- Step 1 (デプロイ後の設定) を参照
- Frontend URLのドメインを Firebase Console > Authentication > Settings に追加

---

## コスト見積もり

### 月額コスト (想定: 100ユーザー/日)

| サービス | スペック | 月額 |
|---------|---------|------|
| **Cloud Run - Frontend** | 1 vCPU, 1GB | $5-10 |
| **Cloud Run - Backend** | 1 vCPU, 1GB | $5-10 |
| **Cloud Run - ADK** | 2 vCPU, 2GB | $10-15 |
| **Firebase (Spark Plan)** | 無料枠 | $0 |
| **Firebase (Blaze Plan)** | 従量課金 | $5-15 |
| **合計** | | **$25-50/月** |

**無料枠 (Cloud Run)**:
- 2百万リクエスト/月
- 360,000 vCPU秒/月
- 180,000 GiB秒/月

---

## 更新デプロイ

コードを更新した後、再デプロイするには:

```bash
# 変更をコミット
git add .
git commit -m "Update: ..."

# 再デプロイ (全サービス)
cd infra
./deploy-cloud-run.sh all

# または個別に
./deploy-cloud-run.sh backend
./deploy-cloud-run.sh frontend
```

---

## ログ確認

```bash
# Backendのログ
gcloud run services logs read hera-backend \
  --region=$GCP_REGION \
  --project=$GCP_PROJECT_ID

# Frontendのログ
gcloud run services logs read hera-frontend \
  --region=$GCP_REGION \
  --project=$GCP_PROJECT_ID

# ADKのログ
gcloud run services logs read hera-adk \
  --region=$GCP_REGION \
  --project=$GCP_PROJECT_ID
```

---

## サポート

問題が発生した場合:

1. エラーメッセージを確認
2. ログを確認 (`gcloud run services logs read ...`)
3. Firebase Consoleでエラーを確認
4. 環境変数が正しく設定されているか確認

---

## Terraform デプロイ (推奨)

TerraformによるInfrastructure as Codeを使用したデプロイ方法です。

### 前提条件

- [Terraform 1.5以上](https://www.terraform.io/downloads)
- Google Cloud SDK (gcloud CLI)
- Firebase プロジェクト設定済み

### Step 1: Terraform のインストール確認

```bash
# Terraformのバージョン確認
terraform --version

# 1.5.0以上であることを確認
```

### Step 2: 環境変数ファイルの作成

```bash
cd infra/terraform/environments/prod

# terraform.tfvars.example をコピー
cp terraform.tfvars.example terraform.tfvars

# terraform.tfvars を編集して環境変数を設定
vim terraform.tfvars
```

`terraform.tfvars` の内容:

```hcl
project_id  = "your-gcp-project-id"
region      = "asia-northeast1"
environment = "prod"

gemini_api_key = "your-gemini-api-key"

firebase_api_key              = "your-firebase-api-key"
firebase_auth_domain          = "your-project.firebaseapp.com"
firebase_project_id           = "your-firebase-project-id"
firebase_storage_bucket       = "your-project.appspot.com"
firebase_messaging_sender_id  = "your-sender-id"
firebase_app_id               = "your-app-id"
```

### Step 3: コンテナイメージのビルド & プッシュ

```bash
# プロジェクトルートに戻る
cd ../../../..

# GCP Project IDを設定
export GCP_PROJECT_ID=your-gcp-project-id

# Artifact Registryリポジトリを作成
gcloud artifacts repositories create hera \
  --repository-format=docker \
  --location=asia-northeast1 \
  --project=$GCP_PROJECT_ID

# Dockerイメージをビルド & プッシュ
# Backend
cd backend
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/hera/hera-backend:latest

# Frontend
cd ../frontend
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/hera/hera-frontend:latest

# ADK
cd ../backend
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/$GCP_PROJECT_ID/hera/hera-adk:latest

cd ..
```

### Step 4: Terraform 初期化

```bash
cd infra/terraform

# Terraformを初期化
terraform init
```

### Step 5: デプロイ計画の確認

```bash
# 変更内容を確認
terraform plan -var-file=environments/prod/terraform.tfvars
```

### Step 6: デプロイ実行

```bash
# デプロイを実行
terraform apply -var-file=environments/prod/terraform.tfvars

# "yes" を入力して実行
```

デプロイには **10-15分** かかります。

### Step 7: デプロイ完了後の確認

```bash
# 出力値を確認
terraform output

# 出力例:
# frontend_url = "https://hera-frontend-prod-xxxxx.run.app"
# backend_url  = "https://hera-backend-prod-xxxxx.run.app"
# adk_url      = "https://hera-adk-prod-xxxxx.run.app"
```

### Terraform 便利コマンド

```bash
# 現在の状態を確認
terraform show

# 特定のリソースを再作成
terraform taint module.backend.google_cloud_run_v2_service.service
terraform apply -var-file=environments/prod/terraform.tfvars

# リソースを削除
terraform destroy -var-file=environments/prod/terraform.tfvars

# フォーマット
terraform fmt -recursive

# 検証
terraform validate
```

---

**デプロイ成功！🎉**
