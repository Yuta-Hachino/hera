#!/bin/bash

# Lint All Script
# リンティング実行

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Running linters...${NC}"

# 仮想環境の有効化
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Python linting (flake8)
echo -e "${BLUE}Linting Python code with flake8...${NC}"
if command -v flake8 &> /dev/null; then
    flake8 backend/ --exclude=.venv,venv,build,dist --max-line-length=100
    echo -e "${GREEN}✓ Python linting passed${NC}"
else
    echo -e "${BLUE}flake8 not installed. Install with: pip install flake8${NC}"
fi

# Python linting (pylint)
echo -e "${BLUE}Linting Python code with pylint...${NC}"
if command -v pylint &> /dev/null; then
    pylint backend/ --ignore=.venv,venv --disable=C0111,R0903
    echo -e "${GREEN}✓ Pylint checks passed${NC}"
else
    echo -e "${BLUE}pylint not installed. Install with: pip install pylint${NC}"
fi

echo -e "${GREEN}✅ Linting completed${NC}"
