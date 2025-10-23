#!/bin/bash

# Start Mock Server Script
# モックAPIサーバーの起動

set -e

cd "$(dirname "$0")"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Starting Mock API Server...${NC}"

# 依存関係のインストールチェック
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    npm install
fi

echo -e "${GREEN}Mock API Server starting on http://localhost:3001${NC}"
echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
echo ""

# カスタムサーバーを起動
npm run start:custom
