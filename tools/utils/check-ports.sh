#!/bin/bash

# Check Ports Script
# 使用中ポートの確認

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Checking common ports...${NC}"

PORTS=(3000 8000 5432 6379 9090 3001)
PORT_NAMES=("Frontend" "Backend" "PostgreSQL" "Redis" "Prometheus" "Grafana")

for i in "${!PORTS[@]}"; do
    PORT=${PORTS[$i]}
    NAME=${PORT_NAMES[$i]}

    if lsof -i :$PORT > /dev/null 2>&1; then
        echo -e "${YELLOW}Port $PORT ($NAME): IN USE${NC}"
        PID=$(lsof -t -i :$PORT)
        echo "  PID: $PID"
        echo "  To kill: kill -9 $PID"
    else
        echo -e "${GREEN}Port $PORT ($NAME): Available${NC}"
    fi
done

echo ""
echo -e "${BLUE}To free a port, run: kill -9 <PID>${NC}"
