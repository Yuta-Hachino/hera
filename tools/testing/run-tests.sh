#!/bin/bash

# Run Tests Script
# 全テストの実行（フロントエンド＋バックエンド）

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Running all tests...${NC}"

# 仮想環境の有効化
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# バックエンドテスト
echo -e "${BLUE}Running backend tests...${NC}"
if [ -d "backend/tests" ]; then
    cd backend
    python -m pytest tests/ -v
    cd ..
    echo -e "${GREEN}✓ Backend tests passed${NC}"
else
    echo -e "${BLUE}No backend tests found${NC}"
fi

echo -e "${GREEN}✅ All tests completed${NC}"
