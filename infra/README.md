# Hera - GCP Cloud Run デプロイガイド

このガイドでは、HeraアプリケーションをGoogle Cloud Platform (Cloud Run)に自動デプロイする方法を説明します。

## 📋 前提条件

デプロイを実行する前に、以下の準備が完了していることを確認してください：

### 1. 必要なツールのインストール

- **gcloud CLI**: [インストールガイド](https://cloud.google.com/sdk/docs/install)
- **Docker Desktop**: [インストールガイド](https://www.docker.com/products/docker-desktop/)

```bash
# バージョン確認
gcloud --version
docker --version
```

**注意**: Terraformは自動インストールされるため、手動インストール不要です。

### 2. GCPプロジェクトの設定

- GCPプロジェクトID: `gen-lang-client-0830629645`
- Firebase プロジェクト: `test-6554c`
- リージョン: `asia-northeast1`

### 3. 必要なGCP APIの有効化 (✓完了済み)

以下のAPIが有効化されていることを確認済みです：

- Cloud Run API
- Cloud Build API
- Artifact Registry API
- Secret Manager API
- IAM API

### 4. 認証情報の配置 (✓完了済み)

- ✅ `backend/firebase-service-account.json` - Firebase Admin SDK用のサービスアカウントキー
- ✅ `infra/terraform/environments/prod/terraform.tfvars` - 環境変数設定ファイル

## 🚀 デプロイ手順（完全自動化）

Google Cloud SDK Dockerコンテナを使用した完全自動デプロイです。

### Step 1: サービスアカウントのセットアップ（初回のみ）

```bash
# infraディレクトリに移動
cd /Users/user/dev/hera/infra

# サービスアカウント自動セットアップを実行
./setup-service-account.sh
```

このスクリプトは以下を自動的に実行します：
- ✅ デプロイ用サービスアカウントの作成
- ✅ 必要なIAM権限の付与
- ✅ サービスアカウントキー（gcp-deploy-key.json）の生成

### Step 2: 完全自動デプロイの実行

```bash
# 完全自動デプロイを実行
./auto-deploy.sh
```

**このスクリプトがDockerコンテナ内で自動的に実行すること：**

1. ✅ サービスアカウントキーで自動認証
2. ✅ Docker認証の設定
3. ✅ Terraformの自動インストール
4. ✅ Artifact Registryリポジトリの作成
5. ✅ Backend Dockerイメージのビルド＆プッシュ
6. ✅ Frontend Dockerイメージのビルド＆プッシュ
7. ✅ Terraformでインフラをデプロイ
8. ✅ デプロイ結果の確認

**所要時間**: 約15-20分

**重要**: すべての処理はDockerコンテナ内で実行されるため、ローカル環境にTerraformをインストールする必要はありません。

### Step 3: デプロイ確認

デプロイが完了すると、以下のURLが表示されます：

```
========================================
デプロイ完了！
========================================

Frontend URL: https://hera-frontend-prod-xxxxx-an.a.run.app
Backend URL:  https://hera-backend-prod-xxxxx-an.a.run.app
ADK URL:      https://hera-adk-prod-xxxxx-an.a.run.app
```

### Step 4: Firebase認証の設定

1. [Firebase Console](https://console.firebase.google.com/project/test-6554c/authentication/providers) にアクセス
2. 「承認済みドメイン」タブを開く
3. デプロイされたFrontend URLのドメインを追加
   - 例: `hera-frontend-prod-xxxxx-an.a.run.app`

### Step 5: 動作確認

```bash
# Frontend URLにアクセス
open https://hera-frontend-prod-xxxxx-an.a.run.app

# Backend APIの動作確認
curl https://hera-backend-prod-xxxxx-an.a.run.app/health
```

## 📊 リソース構成

### Cloud Run サービス

| サービス | CPU | メモリ | 最小インスタンス | 最大インスタンス |
|---------|-----|--------|----------------|----------------|
| Backend | 1 vCPU | 512Mi | 0 | 10 |
| Frontend | 1 vCPU | 512Mi | 0 | 10 |
| ADK | 1 vCPU | 1Gi | 0 | 5 |

### コスト試算

詳細な月額コスト試算は [COST_ESTIMATION.md](./COST_ESTIMATION.md) を参照してください。

- **シナリオA (100ユーザー/月)**: 約$28.04/月
- **シナリオB (1,000ユーザー/月)**: 約$270.80/月
- **シナリオC (10,000ユーザー/月)**: 約$2,698.15/月

## 🔧 トラブルシューティング

### エラー: "Permission denied"

```bash
# gcloud認証を再設定
gcloud auth login
gcloud auth application-default login
```

### エラー: "Docker build failed"

```bash
# Dockerを再起動
# Docker Desktopを再起動してから再実行
./deploy.sh
```

### エラー: "Terraform plan failed"

```bash
# Terraformを再初期化
cd terraform
rm -rf .terraform
terraform init
cd ..
./deploy.sh
```

### エラー: "API not enabled"

```bash
# 必要なAPIを有効化
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

## 🔄 再デプロイ

コードを変更した後に再デプロイする場合：

```bash
cd /Users/user/dev/hera/infra
./deploy.sh
```

スクリプトは既存のリソースを検出し、必要な部分のみ更新します。

## 🌐 カスタムドメインの設定

カスタムドメインを使用する場合は、[CUSTOM_DOMAIN.md](./CUSTOM_DOMAIN.md) を参照してください。

## 📝 その他のドキュメント

- [コスト試算](./COST_ESTIMATION.md) - 詳細なコスト分析
- [カスタムドメイン設定](./CUSTOM_DOMAIN.md) - 独自ドメインの設定方法
- [デプロイマニュアル](./DEPLOY_MANUAL.md) - 手動デプロイ手順

## 💡 開発環境との違い

| 項目 | 開発環境 (ローカル) | 本番環境 (Cloud Run) |
|-----|-------------------|---------------------|
| Backend | Flask開発サーバー | Gunicorn (本番用) |
| Frontend | Next.js dev | Next.js standalone |
| データベース | Firestore | Firestore |
| 認証 | Firebase Auth | Firebase Auth |
| ストレージ | Firebase Storage | Firebase Storage |
| SSL証明書 | なし | Google-managed SSL |
| スケーリング | 固定 | 自動 (0-10インスタンス) |

## 📞 サポート

問題が発生した場合：

1. [GCP Cloud Run ドキュメント](https://cloud.google.com/run/docs)
2. [Firebase ドキュメント](https://firebase.google.com/docs)
3. [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)

---

**最終更新**: 2025-01-07
