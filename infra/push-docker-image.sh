#!/bin/bash
set -e

echo "=== Docker イメージをArtifact Registryにプッシュ ===="

docker run --rm -v /Users/user/dev/hera/backend/firebase-service-account.json:/key.json google/cloud-sdk:latest bash -c "
    gcloud auth activate-service-account --key-file=/key.json 2>/dev/null && \
    gcloud auth configure-docker asia-northeast1-docker.pkg.dev --quiet
"

echo "Pushing Docker image..."
docker push asia-northeast1-docker.pkg.dev/test-6554c/hera/hera-backend:latest

echo ""
echo "✅ Docker イメージのプッシュ完了"
