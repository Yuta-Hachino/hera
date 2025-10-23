#!/bin/bash

# Deploy to Staging Script
# ステージング環境へのデプロイ

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Deploying to staging environment...${NC}"

# 1. テストを実行
echo -e "${BLUE}Step 1: Running tests...${NC}"
./tools/testing/run-tests.sh

# 2. コード品質チェック
echo -e "${BLUE}Step 2: Running code quality checks...${NC}"
./tools/quality/check-all.sh

# 3. Dockerイメージのビルド
echo -e "${BLUE}Step 3: Building Docker images...${NC}"
./tools/docker/docker-build-all.sh

# 4. デプロイ
echo -e "${BLUE}Step 4: Deploying to staging...${NC}"
echo -e "${YELLOW}Note: Configure your staging deployment commands here${NC}"
# docker compose -f docker-compose.staging.yml up -d

echo -e "${GREEN}✅ Deployment to staging completed${NC}"
echo -e "${BLUE}Run health checks: ./tools/deploy/health-check.sh staging${NC}"
