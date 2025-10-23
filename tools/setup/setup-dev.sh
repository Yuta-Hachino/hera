#!/bin/bash

# AI Family Simulator - Complete Development Setup
# 開発環境の完全セットアップスクリプト

set -e

echo "🚀 AI Family Simulator - Complete Development Setup..."

# プロジェクトルートに移動
cd "$(dirname "$0")/../.."

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. 仮想環境の作成
echo -e "${BLUE}Step 1: Creating Python virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment already exists${NC}"
fi

# 仮想環境の有効化
echo -e "${BLUE}Activating virtual environment...${NC}"
source .venv/bin/activate

# 2. 依存関係のインストール
echo -e "${BLUE}Step 2: Installing dependencies...${NC}"
./tools/setup/install-deps.sh

# 3. 環境変数の初期化
echo -e "${BLUE}Step 3: Initializing environment variables...${NC}"
./tools/setup/init-env.sh

# 4. Docker サービスの起動確認
echo -e "${BLUE}Step 4: Checking Docker services...${NC}"
if command -v docker &> /dev/null; then
    if docker compose ps db 2>/dev/null | grep -q "Up"; then
        echo -e "${GREEN}✓ Database is running${NC}"
    else
        echo -e "${YELLOW}⚠ Database is not running. You may want to run: docker compose up -d db redis${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Docker is not available${NC}"
fi

echo ""
echo -e "${GREEN}✅ Development setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit backend/.env with your API keys"
echo "  2. Start services:"
echo "     - Option A: docker compose up -d          # Start all services"
echo "     - Option B: cd backend && adk web agents  # Start ADK agents only"
echo "  3. Start mock server: tools/mock-server/start-mock.sh"
echo ""
echo "Useful commands:"
echo "  - Run tests: tools/testing/run-tests.sh"
echo "  - Format code: tools/quality/format-all.sh"
echo "  - View logs: tools/monitoring/view-logs.sh"
