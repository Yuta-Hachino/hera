# ============================================
# ステージ1: ベースイメージとビルド環境
# ============================================
FROM python:3.11-slim as base

# 作業ディレクトリの設定
WORKDIR /app

# 環境変数の設定
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# ステージ2: 依存関係のインストール
# ============================================
FROM base as dependencies

# requirements.txtをコピー
COPY requirements.txt .

# Python依存関係のインストール
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# ステージ3: 本番用イメージ
# ============================================
FROM base as production

# 依存関係を前のステージからコピー
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# アプリケーションコードをコピー
COPY . /app

# セッションディレクトリ、ログディレクトリの作成
RUN mkdir -p /app/tmp/user_sessions /app/logs

# 非rootユーザーの作成と切り替え
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# ポート8080を公開
EXPOSE 8080

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8080/api/health || exit 1

# アプリケーションの起動
CMD ["python", "api/app.py"]
