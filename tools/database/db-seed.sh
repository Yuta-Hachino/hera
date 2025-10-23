#!/bin/bash

# Database Seed Script
# サンプルデータの投入

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Seeding database with sample data...${NC}"

# 仮想環境の有効化
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Pythonシードスクリプトの実行
if [ -f "backend/scripts/seed.py" ]; then
    cd backend
    python scripts/seed.py
    echo -e "${GREEN}✓ Database seeded successfully${NC}"
else
    echo -e "${BLUE}Note: Seed script not found at backend/scripts/seed.py${NC}"
    echo -e "${BLUE}You may need to create this script${NC}"
fi
