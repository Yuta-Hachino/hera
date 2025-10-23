#!/bin/bash

# Pre-commit Hook Script
# コミット前チェック

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Running pre-commit checks...${NC}"

# 仮想環境の有効化
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 1. コードフォーマットチェック
echo -e "${BLUE}Step 1: Checking code format...${NC}"
if command -v black &> /dev/null; then
    black --check backend/ --exclude=".venv|venv|build|dist" || {
        echo -e "${RED}✗ Code formatting issues found. Run: tools/quality/format-all.sh${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ Code format check passed${NC}"
fi

# 2. リンティング
echo -e "${BLUE}Step 2: Running linters...${NC}"
if command -v flake8 &> /dev/null; then
    flake8 backend/ --exclude=.venv,venv,build,dist --max-line-length=100 || {
        echo -e "${RED}✗ Linting failed${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ Linting passed${NC}"
fi

# 3. テスト実行
echo -e "${BLUE}Step 3: Running tests...${NC}"
if [ -d "backend/tests" ]; then
    cd backend
    python -m pytest tests/ -q || {
        echo -e "${RED}✗ Tests failed${NC}"
        exit 1
    }
    cd ..
    echo -e "${GREEN}✓ Tests passed${NC}"
fi

echo -e "${GREEN}✅ All pre-commit checks passed${NC}"
