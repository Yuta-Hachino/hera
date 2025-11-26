#!/bin/bash

echo "=== Frontend バージョン確認 ==="
echo ""
echo "デプロイされたフロントエンドのバージョンを確認します。"
echo ""

# フロントエンドURLを取得
FRONTEND_URL=$(docker run --rm -v /Users/user/dev/hera/backend/firebase-service-account.json:/key.json google/cloud-sdk:latest bash -c "
    gcloud auth activate-service-account --key-file=/key.json 2>/dev/null && \
    gcloud run services describe hera-frontend-prod \
      --region=asia-northeast1 \
      --project=test-6554c \
      --format='value(status.url)'
")

if [ -z "$FRONTEND_URL" ]; then
    echo "❌ エラー: フロントエンドURLを取得できませんでした"
    exit 1
fi

echo "📍 フロントエンドURL: $FRONTEND_URL"
echo ""
echo "ブラウザでこのURLにアクセスして、コンソール（F12）を開いて"
echo "バージョン情報が表示されることを確認してください。"
echo ""
echo "期待される出力:"
echo "  🚀 AI Family Simulator v0.1.1"
echo "  📋 Build Information (表形式)"
echo ""
echo "また、以下のコマンドでバージョンを確認できます:"
echo "  window.__APP_VERSION__"