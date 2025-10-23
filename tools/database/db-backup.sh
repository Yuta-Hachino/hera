#!/bin/bash

# Database Backup Script
# データベースのバックアップ

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

BACKUP_DIR="backups/database"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ai_family_sim_$TIMESTAMP.sql"

echo -e "${BLUE}Creating database backup...${NC}"

# バックアップディレクトリの作成
mkdir -p "$BACKUP_DIR"

# Docker Composeを使用してバックアップ
if command -v docker &> /dev/null; then
    docker compose exec -T db pg_dump -U postgres ai_family_sim > "$BACKUP_FILE"
    echo -e "${GREEN}✓ Backup created: $BACKUP_FILE${NC}"
else
    echo -e "${RED}Docker not found${NC}"
    exit 1
fi
