#!/bin/bash

# Start Family Agent Script
# 家族エージェントの起動

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Starting Family Agent...${NC}"

# 仮想環境の有効化
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# バックエンドディレクトリに移動
cd backend

# ADK Web UIを起動
echo -e "${BLUE}Launching ADK Web UI...${NC}"
echo -e "${GREEN}Access the UI at: http://localhost:8000${NC}"
echo -e "${BLUE}Select 'family_session_agent' from the available agents${NC}"

adk web agents
