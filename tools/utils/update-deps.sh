#!/bin/bash

# Update Dependencies Script
# 依存関係のアップデート

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Updating dependencies...${NC}"

# 仮想環境の有効化
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Python依存関係のアップデート
echo -e "${BLUE}Updating Python dependencies...${NC}"
pip install --upgrade pip
pip install --upgrade -r backend/requirements.txt
echo -e "${GREEN}✓ Python dependencies updated${NC}"

# 依存関係リストの更新
echo -e "${BLUE}Generating updated requirements.txt...${NC}"
cd backend
pip freeze > requirements.txt
cd ..
echo -e "${GREEN}✓ requirements.txt updated${NC}"

echo -e "${GREEN}✅ Dependencies updated successfully${NC}"
echo -e "${YELLOW}Note: Review changes in requirements.txt before committing${NC}"
