#!/bin/bash

# Heraエージェントから家族フェーズまで一貫テスト実行スクリプト

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Heraエージェントから家族フェーズまで一貫テスト${NC}"
echo "=" * 60

# 仮想環境の有効化
if [ -d ".venv" ]; then
    echo -e "${BLUE}仮想環境を有効化中...${NC}"
    source .venv/bin/activate
fi

# バックエンドディレクトリに移動（testsフォルダから1つ上のディレクトリ）
cd ..

# 必要な依存関係の確認
echo -e "${BLUE}依存関係を確認中...${NC}"
python3 -c "import requests, PIL" 2>/dev/null || {
    echo -e "${RED}必要な依存関係が不足しています。${NC}"
    echo "pip install requests pillow"
    exit 1
}

# APIサーバーが起動しているかチェック
echo -e "${BLUE}APIサーバーの状態を確認中...${NC}"
if ! curl -s http://localhost:8080/api/health > /dev/null; then
    echo -e "${RED}APIサーバーが起動していません。${NC}"
    echo "以下のコマンドでAPIサーバーを起動してください："
    echo "cd backend && python api/app.py"
    exit 1
fi

# ADK Web UIが起動しているかチェック
echo -e "${BLUE}ADK Web UIの状態を確認中...${NC}"
if ! curl -s http://localhost:8000 > /dev/null; then
    echo -e "${RED}ADK Web UIが起動していません。${NC}"
    echo "以下のコマンドでADK Web UIを起動してください："
    echo "cd backend && adk web agents"
    exit 1
fi

# テスト実行
echo -e "${GREEN}テストを実行中...${NC}"
python3 tests/test_full_flow.py

echo -e "${GREEN}✅ テスト完了！${NC}"
