#!/bin/bash

# AI Family Simulator - Install Dependencies
# 全依存関係の一括インストールスクリプト

set -e

echo "🚀 AI Family Simulator - Installing Dependencies..."

# プロジェクトルートに移動
cd "$(dirname "$0")/../.."

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Python バージョンチェック
echo -e "${BLUE}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Python3 is not installed. Please install Python 3.11 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Node.js バージョンチェック
echo -e "${BLUE}Checking Node.js version...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}Node.js is not installed. Please install Node.js 18.0.0 or higher.${NC}"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js $NODE_VERSION found${NC}"

# バックエンド依存関係のインストール
echo -e "${BLUE}Installing backend dependencies...${NC}"
if [ -f "backend/requirements.txt" ]; then
    pip install -r backend/requirements.txt
    echo -e "${GREEN}✓ Backend dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠ backend/requirements.txt not found${NC}"
fi

# モックサーバー依存関係のインストール
echo -e "${BLUE}Installing mock server dependencies...${NC}"
if [ -f "tools/mock-server/package.json" ]; then
    cd tools/mock-server
    npm install
    cd ../..
    echo -e "${GREEN}✓ Mock server dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠ Mock server package.json not found${NC}"
fi

echo -e "${GREEN}✅ All dependencies installed successfully!${NC}"
echo ""
echo "Next steps:"
echo "  1. Run: tools/setup/init-env.sh    # Initialize environment variables"
echo "  2. Run: tools/setup/setup-dev.sh   # Complete development setup"
