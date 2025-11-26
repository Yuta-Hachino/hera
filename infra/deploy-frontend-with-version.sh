#!/bin/bash
set -e

echo "=== Frontend自動バージョン管理デプロイ（Firebase + Live API対応） ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/../frontend"

cd "$FRONTEND_DIR"

# 現在のバージョンを取得
CURRENT_VERSION=$(node -p "require('./package.json').version")
echo "現在のバージョン: $CURRENT_VERSION"

# バージョンを分解
IFS='.' read -r -a VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR=${VERSION_PARTS[0]}
MINOR=${VERSION_PARTS[1]}
PATCH=${VERSION_PARTS[2]}

# パッチバージョンをインクリメント
NEW_PATCH=$((PATCH + 1))
NEW_VERSION="$MAJOR.$MINOR.$NEW_PATCH"
echo "新しいバージョン: $NEW_VERSION"

# package.jsonを更新
node -e "
const fs = require('fs');
const pkg = require('./package.json');
pkg.version = '$NEW_VERSION';
fs.writeFileSync('./package.json', JSON.stringify(pkg, null, 2) + '\\n');
console.log('package.json を更新しました');
"

# Git commit hashを取得
GIT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
echo "Git Commit: $GIT_COMMIT"

# ビルドタイムスタンプを生成
BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "ビルド時刻: $BUILD_TIME"

# Firebase API Keyをシークレットから取得
echo "Firebase APIキーを取得中..."
FIREBASE_API_KEY=$(docker run --rm -v "$SCRIPT_DIR/../backend/firebase-service-account.json:/key.json" google/cloud-sdk:latest bash -c "
    gcloud auth activate-service-account --key-file=/key.json 2>/dev/null && \
    gcloud secrets versions access latest --secret=firebase-api-key-prod --project=test-6554c
")

echo "Firebase API Key取得完了"

# 一時的なcloudbuild.yamlを作成（バージョン情報を含む）
cat > cloudbuild-with-version.yaml <<EOF
steps:
  # ビルド: Dockerイメージをビルド（ビルド引数を指定）
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '--build-arg'
      - 'NEXT_PUBLIC_API_URL=https://hera-backend-prod-716580137550.asia-northeast1.run.app'
      - '--build-arg'
      - 'NEXT_PUBLIC_FIREBASE_API_KEY=$FIREBASE_API_KEY'
      - '--build-arg'
      - 'NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=test-6554c.firebaseapp.com'
      - '--build-arg'
      - 'NEXT_PUBLIC_FIREBASE_PROJECT_ID=test-6554c'
      - '--build-arg'
      - 'NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=test-6554c.firebasestorage.app'
      - '--build-arg'
      - 'NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=716580137550'
      - '--build-arg'
      - 'NEXT_PUBLIC_FIREBASE_APP_ID=1:716580137550:web:754d37c7f4f51b3363b11f'
      - '--build-arg'
      - 'NEXT_PUBLIC_BUILD_TIME=$BUILD_TIME'
      - '--build-arg'
      - 'NEXT_PUBLIC_GIT_COMMIT=$GIT_COMMIT'
      - '--build-arg'
      - 'NEXT_PUBLIC_VERSION=$NEW_VERSION'
      - '-t'
      - 'asia-northeast1-docker.pkg.dev/test-6554c/hera/hera-frontend:latest'
      - '-t'
      - 'asia-northeast1-docker.pkg.dev/test-6554c/hera/hera-frontend:v$NEW_VERSION'
      - '-t'
      - 'asia-northeast1-docker.pkg.dev/test-6554c/hera/hera-frontend:\$BUILD_ID'
      - '.'

  # プッシュ: Dockerイメージをプッシュ
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'asia-northeast1-docker.pkg.dev/test-6554c/hera/hera-frontend:latest'

  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'asia-northeast1-docker.pkg.dev/test-6554c/hera/hera-frontend:v$NEW_VERSION'

  # デプロイ: Cloud Runにデプロイ
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'hera-frontend-prod'
      - '--image'
      - 'asia-northeast1-docker.pkg.dev/test-6554c/hera/hera-frontend:latest'
      - '--platform=managed'
      - '--region=asia-northeast1'
      - '--port=3000'
      - '--cpu=1'
      - '--memory=512Mi'
      - '--timeout=60'
      - '--min-instances=0'
      - '--max-instances=5'
      - '--allow-unauthenticated'

images:
  - 'asia-northeast1-docker.pkg.dev/test-6554c/hera/hera-frontend:latest'
  - 'asia-northeast1-docker.pkg.dev/test-6554c/hera/hera-frontend:v$NEW_VERSION'
  - 'asia-northeast1-docker.pkg.dev/test-6554c/hera/hera-frontend:\$BUILD_ID'

options:
  machineType: 'E2_HIGHCPU_8'
  logging: CLOUD_LOGGING_ONLY
EOF

echo ""
echo "=== Cloud Build経由でデプロイ開始 ==="
echo ""

# Cloud Build経由でデプロイ
docker run --rm \
  -v "$PWD":/workspace \
  -v "$SCRIPT_DIR/../backend/firebase-service-account.json":/key.json \
  -w /workspace \
  google/cloud-sdk:latest bash -c "
    gcloud auth activate-service-account --key-file=/key.json 2>/dev/null && \
    gcloud builds submit \
      --config=cloudbuild-with-version.yaml \
      --project=test-6554c \
      --region=asia-northeast1 \
      .
"

# 一時ファイルをクリーンアップ
rm -f cloudbuild-with-version.yaml

# Gitにバージョン変更をコミット（オプション）
echo ""
echo "=== バージョン更新をコミット ==="
git add package.json
git commit -m "chore: bump version to $NEW_VERSION" || echo "バージョン変更のコミットをスキップ（変更なしまたはGit設定なし）"

echo ""
echo "=== Frontend デプロイ完了 ==="
echo ""
echo "✅ デプロイ完了:"
echo "  - バージョン: $NEW_VERSION"
echo "  - Git Commit: ${GIT_COMMIT:0:7}"
echo "  - ビルド時刻: $BUILD_TIME"
echo ""
echo "サービスURL確認:"
docker run --rm -v "$SCRIPT_DIR/../backend/firebase-service-account.json:/key.json" google/cloud-sdk:latest bash -c "
    gcloud auth activate-service-account --key-file=/key.json 2>/dev/null && \
    gcloud run services describe hera-frontend-prod \
      --region=asia-northeast1 \
      --project=test-6554c \
      --format='value(status.url)'
"