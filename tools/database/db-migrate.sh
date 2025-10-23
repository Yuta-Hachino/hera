#!/bin/bash

# Database Migration Script
# データベースマイグレーションの実行

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Running database migrations...${NC}"

# 仮想環境の有効化
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Alembicマイグレーションの実行
if [ -d "backend/alembic" ]; then
    cd backend
    python -m alembic upgrade head
    echo -e "${GREEN}✓ Database migration completed${NC}"
else
    echo -e "${BLUE}Note: Alembic not configured yet${NC}"
fi
