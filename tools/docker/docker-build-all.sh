#!/bin/bash

# Docker Build All Script
# 全サービスのDockerイメージをビルド

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Building all Docker images...${NC}"

docker compose build

echo -e "${GREEN}✓ All Docker images built successfully${NC}"
