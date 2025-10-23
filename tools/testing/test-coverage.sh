#!/bin/bash

# Test Coverage Script
# カバレッジレポート生成

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Running tests with coverage...${NC}"

# 仮想環境の有効化
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# バックエンドカバレッジ
echo -e "${BLUE}Backend coverage report...${NC}"
if [ -d "backend/tests" ]; then
    cd backend
    python -m pytest --cov=. --cov-report=html --cov-report=term tests/
    echo -e "${GREEN}✓ Coverage report generated at backend/htmlcov/index.html${NC}"
    cd ..
fi

echo -e "${GREEN}✅ Coverage reports generated${NC}"
