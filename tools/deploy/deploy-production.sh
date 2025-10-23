#!/bin/bash

# Deploy to Production Script
# 本番環境へのデプロイ

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}⚠ WARNING: Deploying to PRODUCTION!${NC}"
read -p "Are you sure you want to deploy to production? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo -e "${BLUE}Deploying to production environment...${NC}"

# 1. テストを実行
echo -e "${BLUE}Step 1: Running tests...${NC}"
./tools/testing/run-tests.sh

# 2. コード品質チェック
echo -e "${BLUE}Step 2: Running code quality checks...${NC}"
./tools/quality/check-all.sh

# 3. Dockerイメージのビルド
echo -e "${BLUE}Step 3: Building Docker images...${NC}"
./tools/docker/docker-build-all.sh

# 4. データベースバックアップ
echo -e "${BLUE}Step 4: Creating database backup...${NC}"
./tools/database/db-backup.sh

# 5. デプロイ
echo -e "${BLUE}Step 5: Deploying to production...${NC}"
echo -e "${YELLOW}Note: Configure your production deployment commands here${NC}"
# docker compose -f docker-compose.production.yml up -d

echo -e "${GREEN}✅ Deployment to production completed${NC}"
echo -e "${BLUE}Run health checks: ./tools/deploy/health-check.sh production${NC}"
