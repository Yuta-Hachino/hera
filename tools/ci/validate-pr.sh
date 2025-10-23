#!/bin/bash

# Validate Pull Request Script
# PRバリデーション

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Validating Pull Request...${NC}"

# 1. ブランチ名チェック
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "${BLUE}Current branch: $BRANCH${NC}"

if [[ $BRANCH == "main" ]] || [[ $BRANCH == "master" ]]; then
    echo -e "${RED}✗ Cannot create PR from main/master branch${NC}"
    exit 1
fi

# 2. コード品質チェック
echo -e "${BLUE}Running code quality checks...${NC}"
./tools/quality/check-all.sh

# 3. テスト実行
echo -e "${BLUE}Running all tests...${NC}"
./tools/testing/run-tests.sh

# 4. ビルドチェック
echo -e "${BLUE}Checking if project builds...${NC}"
if [ -f "docker-compose.yml" ]; then
    docker compose build --quiet
    echo -e "${GREEN}✓ Build successful${NC}"
fi

echo -e "${GREEN}✅ PR validation passed${NC}"
echo -e "${BLUE}You can now create your pull request${NC}"
