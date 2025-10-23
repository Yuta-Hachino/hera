#!/bin/bash

# Docker Clean Script
# 未使用のDockerイメージ・コンテナをクリーンアップ

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Cleaning up Docker resources...${NC}"

# 停止中のコンテナを削除
echo -e "${BLUE}Removing stopped containers...${NC}"
docker compose down

# 未使用のイメージを削除
echo -e "${BLUE}Removing unused images...${NC}"
docker image prune -f

# 未使用のボリュームを削除（注意が必要）
read -p "Do you want to remove unused volumes? This may delete data (yes/no): " -r
if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    docker volume prune -f
    echo -e "${GREEN}✓ Volumes cleaned${NC}"
fi

# 未使用のネットワークを削除
echo -e "${BLUE}Removing unused networks...${NC}"
docker network prune -f

echo -e "${GREEN}✓ Docker cleanup completed${NC}"
