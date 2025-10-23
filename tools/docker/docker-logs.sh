#!/bin/bash

# Docker Logs Script
# 特定サービスのログを表示

set -e

cd "$(dirname "$0")/../.."

BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo -e "${BLUE}Available services:${NC}"
    docker compose ps --services
    echo ""
    echo -e "${BLUE}Usage: $0 <service_name> [--follow]${NC}"
    echo "Example: $0 backend --follow"
    exit 1
fi

SERVICE=$1
FOLLOW_FLAG=""

if [ "$2" == "--follow" ] || [ "$2" == "-f" ]; then
    FOLLOW_FLAG="-f"
fi

echo -e "${BLUE}Showing logs for $SERVICE...${NC}"
docker compose logs $FOLLOW_FLAG "$SERVICE"
