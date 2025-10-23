#!/bin/bash

# Build and Test Pipeline Script
# ビルド＆テストパイプライン

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Running CI/CD Pipeline...${NC}"

# 1. 環境チェック
echo -e "${BLUE}Step 1: Checking environment...${NC}"
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment found${NC}"
else
    echo -e "${RED}✗ Virtual environment not found${NC}"
    exit 1
fi

# 2. 依存関係のインストール
echo -e "${BLUE}Step 2: Installing dependencies...${NC}"
./tools/setup/install-deps.sh

# 3. コード品質チェック
echo -e "${BLUE}Step 3: Running code quality checks...${NC}"
./tools/quality/check-all.sh

# 4. テスト実行
echo -e "${BLUE}Step 4: Running tests...${NC}"
./tools/testing/run-tests.sh

# 5. カバレッジレポート生成
echo -e "${BLUE}Step 5: Generating coverage report...${NC}"
./tools/testing/test-coverage.sh

# 6. ビルド
echo -e "${BLUE}Step 6: Building Docker images...${NC}"
./tools/docker/docker-build-all.sh

echo -e "${GREEN}✅ CI/CD Pipeline completed successfully${NC}"
