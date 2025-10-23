#!/bin/bash

# Docker Restart Script
# サービスの再起動

set -e

cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo -e "${BLUE}Restarting all services...${NC}"
    docker compose restart
    echo -e "${GREEN}✓ All services restarted${NC}"
else
    SERVICE=$1
    echo -e "${BLUE}Restarting $SERVICE...${NC}"
    docker compose restart "$SERVICE"
    echo -e "${GREEN}✓ $SERVICE restarted${NC}"
fi
