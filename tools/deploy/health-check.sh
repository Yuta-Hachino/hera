#!/bin/bash

# Health Check Script
# デプロイ後のヘルスチェック

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

ENV=${1:-development}

echo -e "${BLUE}Running health checks for $ENV environment...${NC}"

# バックエンドヘルスチェック
echo -e "${BLUE}Checking backend API...${NC}"
if [ "$ENV" = "production" ]; then
    API_URL="https://api.production.example.com"
elif [ "$ENV" = "staging" ]; then
    API_URL="https://api.staging.example.com"
else
    API_URL="http://localhost:8000"
fi

if curl -f -s "${API_URL}/v1/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend API is healthy${NC}"
else
    echo -e "${RED}✗ Backend API is not responding${NC}"
fi

# データベース接続チェック
echo -e "${BLUE}Checking database connection...${NC}"
if docker compose exec -T db pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database is healthy${NC}"
else
    echo -e "${RED}✗ Database is not responding${NC}"
fi

# Redis接続チェック
echo -e "${BLUE}Checking Redis connection...${NC}"
if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is healthy${NC}"
else
    echo -e "${RED}✗ Redis is not responding${NC}"
fi

echo -e "${GREEN}✅ Health checks completed${NC}"
