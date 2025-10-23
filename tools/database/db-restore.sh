#!/bin/bash

# Database Restore Script
# データベースのリストア

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo -e "${RED}Usage: $0 <backup_file>${NC}"
    echo -e "${BLUE}Available backups:${NC}"
    ls -1 backups/database/*.sql 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}⚠ WARNING: This will replace all current data!${NC}"
read -p "Are you sure you want to restore from $BACKUP_FILE? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo -e "${BLUE}Restoring database from $BACKUP_FILE...${NC}"

# Docker Composeを使用してリストア
if command -v docker &> /dev/null; then
    cat "$BACKUP_FILE" | docker compose exec -T db psql -U postgres ai_family_sim
    echo -e "${GREEN}✓ Database restored successfully${NC}"
else
    echo -e "${RED}Docker not found${NC}"
    exit 1
fi
