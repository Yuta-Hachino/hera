# サービスアカウント設定ガイド

完全自動デプロイを実現するため、サービスアカウントキーを使用します。

## 📋 サービスアカウントキーの作成

### Step 1: サービスアカウントの作成

```bash
# サービスアカウントを作成
gcloud iam service-accounts create hera-deploy \
  --display-name="Hera Deploy Service Account" \
  --project=gen-lang-client-0830629645

# 作成されたサービスアカウントのメールアドレスを確認
gcloud iam service-accounts list --project=gen-lang-client-0830629645
```

### Step 2: 必要な権限を付与

```bash
# プロジェクトID
PROJECT_ID="gen-lang-client-0830629645"

# サービスアカウントのメールアドレス
SA_EMAIL="hera-deploy@${PROJECT_ID}.iam.gserviceaccount.com"

# 必要な権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/artifactregistry.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/iam.securityAdmin"
```

### Step 3: サービスアカウントキーの作成

```bash
# キーを作成してダウンロード
gcloud iam service-accounts keys create \
  /Users/user/dev/hera/infra/gcp-deploy-key.json \
  --iam-account=hera-deploy@gen-lang-client-0830629645.iam.gserviceaccount.com \
  --project=gen-lang-client-0830629645
```

**重要**: このキーファイルは機密情報です。Gitにコミットしないでください。

### Step 4: キーファイルの配置確認

```bash
# キーファイルが正しく配置されているか確認
ls -la /Users/user/dev/hera/infra/gcp-deploy-key.json
```

## 🔐 セキュリティ

- `gcp-deploy-key.json` は `.gitignore` に追加済みです
- このキーは本番環境デプロイ専用です
- 定期的にキーをローテーションしてください

## ✅ 確認

キーファイルの作成後、以下のコマンドでデプロイを実行できます：

```bash
cd /Users/user/dev/hera/infra
./auto-deploy.sh
```
