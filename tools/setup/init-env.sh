#!/bin/bash

# AI Family Simulator - Initialize Environment Variables
# 環境変数ファイルの初期化スクリプト

set -e

echo "🔧 AI Family Simulator - Initializing Environment Variables..."

# プロジェクトルートに移動
cd "$(dirname "$0")/../.."

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# バックエンド .env ファイルの作成
if [ -f "backend/.env" ]; then
    echo -e "${YELLOW}⚠ backend/.env already exists. Skipping...${NC}"
else
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
        echo -e "${GREEN}✓ Created backend/.env from .env.example${NC}"
        echo -e "${YELLOW}⚠ Please edit backend/.env and set your API keys${NC}"
    else
        echo -e "${YELLOW}⚠ backend/.env.example not found${NC}"
    fi
fi

# ルート .env ファイルの作成（Docker Compose用）
if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠ .env already exists. Skipping...${NC}"
else
    cat > .env << 'EOF'
# AI Family Simulator Environment Variables

# API Keys
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# JWT Secret
JWT_SECRET_KEY=your_jwt_secret_key_here

# AWS Credentials (Optional)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
S3_BUCKET=your_s3_bucket

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_family_sim

# Redis
REDIS_URL=redis://localhost:6379

# Environment
NODE_ENV=development
EOF
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo -e "${YELLOW}⚠ Please edit .env and set your actual values${NC}"
fi

echo -e "${GREEN}✅ Environment initialization complete!${NC}"
echo ""
echo "Important: Edit the following files with your API keys:"
echo "  - backend/.env"
echo "  - .env"
