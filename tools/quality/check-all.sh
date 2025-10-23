#!/bin/bash

# Check All Script
# フォーマット、リント、型チェックの一括実行

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Running all code quality checks...${NC}"

# フォーマットチェック
echo -e "${BLUE}Step 1: Formatting code...${NC}"
./tools/quality/format-all.sh

# リンティング
echo -e "${BLUE}Step 2: Running linters...${NC}"
./tools/quality/lint-all.sh

# 型チェック
echo -e "${BLUE}Step 3: Running type checks...${NC}"
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

if command -v mypy &> /dev/null; then
    mypy backend/ --ignore-missing-imports
    echo -e "${GREEN}✓ Type checking passed${NC}"
else
    echo -e "${BLUE}mypy not installed. Install with: pip install mypy${NC}"
fi

echo -e "${GREEN}✅ All quality checks passed${NC}"
