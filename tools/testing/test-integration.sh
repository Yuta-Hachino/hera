#!/bin/bash

# Integration Test Script
# 統合テストの実行

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Running integration tests...${NC}"

# Dockerサービスが起動しているか確認
if ! docker compose ps | grep -q "Up"; then
    echo -e "${YELLOW}Starting Docker services...${NC}"
    docker compose up -d
    sleep 5
fi

# 仮想環境の有効化
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 統合テストの実行
if [ -d "backend/tests/integration" ]; then
    cd backend
    python -m pytest tests/integration/ -v
    cd ..
    echo -e "${GREEN}✓ Integration tests passed${NC}"
else
    echo -e "${BLUE}No integration tests found${NC}"
fi

echo -e "${GREEN}✅ Integration tests completed${NC}"
