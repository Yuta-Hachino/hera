#!/bin/bash

# Clean Sessions Script
# 古いセッションデータのクリーンアップ

set -e

cd "$(dirname "$0")/../.."

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SESSION_DIR="backend/tmp/user_sessions"

echo -e "${YELLOW}⚠ WARNING: This will delete old session data!${NC}"

# オプション: 日数指定
DAYS=${1:-7}
echo -e "${BLUE}Cleaning sessions older than $DAYS days...${NC}"

read -p "Are you sure you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Aborted."
    exit 0
fi

if [ -d "$SESSION_DIR" ]; then
    # $DAYS日より古いセッションを削除
    find "$SESSION_DIR" -mindepth 1 -maxdepth 1 -type d -mtime +$DAYS -exec rm -rf {} \;
    echo -e "${GREEN}✓ Old sessions cleaned${NC}"
else
    echo -e "${BLUE}No session directory found${NC}"
fi
