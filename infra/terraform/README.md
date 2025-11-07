# Hera - Terraform Infrastructure

TerraformによるHeraアプリのインフラストラクチャ管理です。

## ディレクトリ構成

```
terraform/
├── main.tf                 # メインのリソース定義
├── variables.tf            # 変数定義
├── outputs.tf              # 出力定義
├── provider.tf             # プロバイダー設定
├── versions.tf             # Terraformとプロバイダーのバージョン
├── modules/
│   ├── cloud-run/         # Cloud Runサービスモジュール
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── secrets/           # Secret Managerモジュール
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── environments/
    ├── dev/               # 開発環境
    │   └── terraform.tfvars.example
    └── prod/              # 本番環境
        └── terraform.tfvars.example
```

## デプロイされるリソース

### GCP サービス

- **Cloud Run**: Backend, Frontend, ADKサービス
- **Secret Manager**: 環境変数の安全な管理
- **Service Account**: Cloud Runサービス用のアカウント
- **IAM Bindings**: 必要な権限の付与

### 管理されるシークレット

- Gemini API Key
- Firebase API Key
- その他の機密情報

## セットアップ

### 1. 環境変数ファイルの作成

```bash
# 本番環境の場合
cd environments/prod
cp terraform.tfvars.example terraform.tfvars

# 開発環境の場合
cd environments/dev
cp terraform.tfvars.example terraform.tfvars
```

`terraform.tfvars` を編集して、必要な変数を設定します。

### 2. Terraformの初期化

```bash
cd infra/terraform
terraform init
```

### 3. デプロイ計画の確認

```bash
# 本番環境
terraform plan -var-file=environments/prod/terraform.tfvars

# 開発環境
terraform plan -var-file=environments/dev/terraform.tfvars
```

### 4. デプロイ実行

```bash
# 本番環境
terraform apply -var-file=environments/prod/terraform.tfvars

# 開発環境
terraform apply -var-file=environments/dev/terraform.tfvars
```

## 環境別の設定

### Development (dev)

- 最小インスタンス数: 0 (コスト削減のためスケールゼロ)
- 最大インスタンス数: 5
- リソース: 小さめ (512Mi メモリ)

### Production (prod)

- 最小インスタンス数: 1 (常時稼働)
- 最大インスタンス数: 20
- リソース: 標準 (1Gi メモリ)

## よく使うコマンド

```bash
# 現在の状態を確認
terraform show

# 出力値を確認
terraform output

# 特定のリソースの状態を確認
terraform state show module.backend.google_cloud_run_v2_service.service

# フォーマット
terraform fmt -recursive

# 検証
terraform validate

# リソースを削除
terraform destroy -var-file=environments/prod/terraform.tfvars
```

## モジュールの使用方法

### Cloud Run モジュール

```hcl
module "my_service" {
  source = "./modules/cloud-run"

  service_name = "my-service"
  region       = "asia-northeast1"
  image        = "gcr.io/project-id/my-service:latest"

  cpu    = "1"
  memory = "1Gi"

  env_vars = {
    ENV_VAR = "value"
  }

  secret_env_vars = {
    API_KEY = {
      secret  = "projects/123/secrets/api-key"
      version = "latest"
    }
  }
}
```

### Secret Manager モジュール

```hcl
module "my_secret" {
  source = "./modules/secrets"

  secret_id    = "my-secret"
  secret_value = var.my_secret_value

  service_account_email = google_service_account.cloud_run.email
}
```

## トラブルシューティング

### エラー: API not enabled

```bash
# 必要なAPIを手動で有効化
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### エラー: Image not found

Dockerイメージをビルドしてプッシュする必要があります:

```bash
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/PROJECT_ID/hera/hera-backend:latest
```

### State ロックエラー

```bash
# 強制的にロックを解除 (注意して使用)
terraform force-unlock LOCK_ID
```

## State 管理

初回はローカルでstateを管理します。本番環境では、GCSバケットでstateを管理することを推奨します。

### GCS Backend の設定

`versions.tf` で以下のコメントを外してください:

```hcl
backend "gcs" {
  bucket = "hera-terraform-state"
  prefix = "terraform/state"
}
```

その後、stateを移行:

```bash
terraform init -migrate-state
```

## セキュリティ

- `terraform.tfvars` ファイルは .gitignore に含まれています
- 機密情報はSecret Managerで管理されます
- terraform.tfstate には機密情報が含まれる可能性があるため、適切に保護してください

## 参考資料

- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
