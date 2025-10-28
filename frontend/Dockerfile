# ============================================
# ステージ1: 依存関係のインストール
# ============================================
FROM node:18-alpine AS dependencies

WORKDIR /app

# package.jsonとpackage-lock.jsonをコピー
COPY package*.json ./

# 依存関係のインストール
RUN npm ci

# ============================================
# ステージ2: ビルド
# ============================================
FROM node:18-alpine AS builder

WORKDIR /app

# 依存関係を前のステージからコピー
COPY --from=dependencies /app/node_modules ./node_modules

# ソースコードをコピー
COPY . .

# ビルド引数としてAPIのURLを受け取る
ARG NEXT_PUBLIC_API_URL=http://localhost:8080
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Next.jsアプリケーションをビルド
RUN npm run build

# ============================================
# ステージ3: 本番用イメージ
# ============================================
FROM node:18-alpine AS production

WORKDIR /app

# 非rootユーザーの作成
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# 必要なファイルのみコピー
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# 非rootユーザーに切り替え
USER nextjs

# ポート3000を公開
EXPOSE 3000

# 環境変数
ENV PORT=3000 \
    NODE_ENV=production

# Next.jsアプリケーションの起動
CMD ["node", "server.js"]
