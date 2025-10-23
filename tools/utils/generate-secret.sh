#!/bin/bash

# Generate Secret Script
# JWT秘密鍵などの生成

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Generating secure secret key...${NC}"

# OpenSSLを使用してランダムな秘密鍵を生成
SECRET=$(openssl rand -hex 32)

echo -e "${GREEN}Generated secret key:${NC}"
echo "$SECRET"
echo ""
echo -e "${BLUE}Add this to your .env file:${NC}"
echo "JWT_SECRET_KEY=$SECRET"
