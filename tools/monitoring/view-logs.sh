#!/bin/bash

# View Logs Script
# 各サービスのログを表示

set -e

cd "$(dirname "$0")/../.."

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}Available services:${NC}"
echo "1. backend"
echo "2. db (database)"
echo "3. redis"
echo "4. agents"
echo "5. all"
echo ""

if [ -z "$1" ]; then
    read -p "Select service (1-5): " choice
else
    choice=$1
fi

case $choice in
    1|backend)
        echo -e "${GREEN}Showing backend logs...${NC}"
        docker compose logs -f backend
        ;;
    2|db|database)
        echo -e "${GREEN}Showing database logs...${NC}"
        docker compose logs -f db
        ;;
    3|redis)
        echo -e "${GREEN}Showing Redis logs...${NC}"
        docker compose logs -f redis
        ;;
    4|agents)
        echo -e "${GREEN}Showing agents logs...${NC}"
        docker compose logs -f agents
        ;;
    5|all)
        echo -e "${GREEN}Showing all logs...${NC}"
        docker compose logs -f
        ;;
    *)
        echo "Invalid selection"
        exit 1
        ;;
esac
