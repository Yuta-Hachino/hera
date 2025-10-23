#!/bin/bash

# Cleanup Temporary Files Script
# 一時ファイルのクリーンアップ

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Cleaning up temporary files...${NC}"

# Python キャッシュファイルの削除
echo -e "${BLUE}Removing Python cache files...${NC}"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo -e "${GREEN}✓ Python cache cleaned${NC}"

# ビルド成果物の削除
echo -e "${BLUE}Removing build artifacts...${NC}"
rm -rf backend/build backend/dist backend/*.egg-info 2>/dev/null || true
echo -e "${GREEN}✓ Build artifacts cleaned${NC}"

# カバレッジレポートの削除
echo -e "${BLUE}Removing coverage reports...${NC}"
rm -rf backend/htmlcov backend/.coverage 2>/dev/null || true
echo -e "${GREEN}✓ Coverage reports cleaned${NC}"

# ログファイルの削除（オプション）
read -p "Do you want to remove log files? (yes/no): " -r
if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    find . -name "*.log" -delete 2>/dev/null || true
    echo -e "${GREEN}✓ Log files cleaned${NC}"
fi

echo -e "${GREEN}✅ Cleanup completed${NC}"
