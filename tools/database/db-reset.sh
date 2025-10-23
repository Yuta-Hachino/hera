#!/bin/bash

# Database Reset Script
# データベースのリセット（注意: 全データが削除されます）

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}⚠ WARNING: This will delete all data in the database!${NC}"
read -p "Are you sure you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo -e "${YELLOW}Resetting database...${NC}"

# Docker Composeでデータベースを再起動
if command -v docker &> /dev/null; then
    docker compose down db
    docker volume rm geechs-ai-hackathon-202510-team-a_postgres_data 2>/dev/null || true
    docker compose up -d db

    echo -e "${YELLOW}Waiting for database to be ready...${NC}"
    sleep 5

    # マイグレーションの実行
    ./tools/database/db-migrate.sh

    echo -e "${GREEN}✓ Database reset completed${NC}"
else
    echo -e "${RED}Docker not found${NC}"
    exit 1
fi
