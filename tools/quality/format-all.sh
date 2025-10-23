#!/bin/bash

# Format All Script
# 全コードのフォーマット

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Formatting all code...${NC}"

# 仮想環境の有効化
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Pythonコードのフォーマット（Black）
echo -e "${BLUE}Formatting Python code with Black...${NC}"
if command -v black &> /dev/null; then
    black backend/ --exclude=".venv|venv|build|dist"
    echo -e "${GREEN}✓ Python code formatted${NC}"
else
    echo -e "${BLUE}Black not installed. Install with: pip install black${NC}"
fi

# Pythonインポートの整理（isort）
echo -e "${BLUE}Sorting Python imports with isort...${NC}"
if command -v isort &> /dev/null; then
    isort backend/ --skip .venv --skip venv
    echo -e "${GREEN}✓ Python imports sorted${NC}"
else
    echo -e "${BLUE}isort not installed. Install with: pip install isort${NC}"
fi

echo -e "${GREEN}✅ Code formatting completed${NC}"
