#!/bin/bash
# このスクリプトはキー作成とデプロイを自動実行します

set -e

cd /Users/user/dev/hera/infra

echo "=========================================="
echo "サービスアカウントキー作成中..."
echo "=========================================="

# キーを作成
gcloud iam service-accounts keys create \
  /Users/user/dev/hera/infra/gcp-deploy-key.json \
  --iam-account=hera-deploy@gen-lang-client-0830629645.iam.gserviceaccount.com \
  --project=gen-lang-client-0830629645

echo "✓ キー作成完了"
echo ""
echo "=========================================="
echo "自動デプロイを開始します..."
echo "=========================================="
echo ""

# デプロイ実行
./auto-deploy.sh
