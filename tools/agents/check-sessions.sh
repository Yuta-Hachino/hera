#!/bin/bash

# Check Sessions Script
# セッションデータの確認

set -e

cd "$(dirname "$0")/../.."

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

SESSION_DIR="backend/tmp/user_sessions"

echo -e "${BLUE}Checking session data...${NC}"

if [ -d "$SESSION_DIR" ]; then
    echo -e "${GREEN}Session directory: $SESSION_DIR${NC}"
    echo ""

    # セッション数をカウント
    SESSION_COUNT=$(find "$SESSION_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l)
    echo -e "${BLUE}Total sessions: $SESSION_COUNT${NC}"
    echo ""

    # 各セッションの詳細を表示
    for session in "$SESSION_DIR"/*; do
        if [ -d "$session" ]; then
            echo -e "${GREEN}Session: $(basename "$session")${NC}"
            if [ -f "$session/user_profile.json" ]; then
                echo "  ✓ user_profile.json"
            fi
            if [ -f "$session/family_plan.json" ]; then
                echo "  ✓ family_plan.json"
            fi
            echo ""
        fi
    done
else
    echo -e "${BLUE}No session directory found at $SESSION_DIR${NC}"
fi
