# コンテナネットワーク設定 検証レポート

**検証日**: 2025-10-28
**対象**: Docker Compose 設定ファイル群のコンテナ間接続設定

---

## ✅ 検証結果サマリー

すべてのコンテナ間接続設定は**正しく構成されています**。

| 項目 | 状態 | 詳細 |
|-----|------|------|
| Redis接続設定 | ✅ 正常 | サービス名とURL一致 |
| Frontend→Backend | ✅ 正常 | ポートマッピング正常 |
| ネットワーク構成 | ✅ 正常 | 全サービスが同一ネットワーク |
| CORS設定 | ✅ 正常 | オリジン設定適切 |
| 依存関係チェーン | ✅ 正常 | 起動順序正しい |

---

## 1. Redis接続設定の検証

### ✅ docker-compose.redis.yml

**Backend設定** (backend/api/app.py:19-30):
```yaml
environment:
  - REDIS_URL=redis://redis:6379/0
```

**ADK設定** (backend/api/app.py:48-56):
```yaml
environment:
  - REDIS_URL=redis://redis:6379/0
```

**Redisサービス定義** (backend/api/app.py:80-82):
```yaml
redis:
  image: redis:7-alpine
  container_name: hera-redis
```

**検証結果**:
- ✅ サービス名 `redis` と接続URL `redis://redis:6379/0` が一致
- ✅ 全サービスが `hera-network` に接続
- ✅ Backend と ADK の両方が Redis に依存関係設定済み

### ✅ docker-compose.production.yml

**Backend設定** (docker-compose.production.yml:30):
```yaml
environment:
  - REDIS_URL=redis://redis:6379/0
```

**Redisサービス定義** (docker-compose.production.yml:57-59):
```yaml
redis:
  image: redis:7-alpine
  container_name: hera-redis
```

**検証結果**:
- ✅ サービス名とURL一致
- ✅ Backend が Redis に依存関係設定済み
- ⚠️ **注意**: ADK サービスは production.yml に含まれていない（設計通り）

---

## 2. Frontend → Backend API 接続設定

### ✅ 接続パターン

```
Browser (localhost)
  ↓
http://localhost:3000 (Frontend Container - port mapping)
  ↓
http://localhost:8080 (Backend Container - port mapping)
```

### ✅ 環境変数設定

**docker-compose.yml & docker-compose.redis.yml**:
```yaml
frontend:
  environment:
    - NEXT_PUBLIC_API_URL=http://localhost:8080
  build:
    args:
      NEXT_PUBLIC_API_URL=http://localhost:8080
```

**docker-compose.production.yml**:
```yaml
frontend:
  environment:
    - NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
  build:
    args:
      NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
```

### ✅ Frontend実装確認 (frontend/lib/api.ts:10)

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
```

**検証結果**:
- ✅ `NEXT_PUBLIC_API_URL` は browser-side で使用される（SSRなし）
- ✅ Browser → `localhost:8080` → Host port mapping → Backend container ✅
- ✅ ポートマッピングが正しく設定されている:
  - Backend: `"8080:8080"`
  - Frontend: `"3000:3000"`

**重要な考察**:
- 現在のフロントエンドは **Client-Side Rendering (CSR) のみ**
- `getServerSideProps` や `getStaticProps` は使用されていない
- そのため、コンテナ内部の名前解決（`http://backend:8080`）は不要
- ブラウザから直接 `localhost:8080` に接続するため、ポートマッピングが機能する

---

## 3. ネットワーク構成の一貫性

### ✅ docker-compose.yml (ローカル開発)

```yaml
services:
  backend:
    networks: [hera-network]
  adk:
    networks: [hera-network]
  frontend:
    networks: [hera-network]

networks:
  hera-network:
    driver: bridge
```

### ✅ docker-compose.redis.yml

```yaml
services:
  backend:
    networks: [hera-network]
  adk:
    networks: [hera-network]
  redis:
    networks: [hera-network]
  frontend:
    networks: [hera-network]

networks:
  hera-network:
    driver: bridge
```

### ✅ docker-compose.production.yml

```yaml
services:
  backend:
    networks: [hera-network]
  redis:
    networks: [hera-network]
  frontend:
    networks: [hera-network]

networks:
  hera-network:
    driver: bridge
```

**検証結果**:
- ✅ 全docker-composeファイルで同一ネットワーク名を使用
- ✅ 全サービスが同一bridgeネットワークに接続
- ✅ コンテナ間でサービス名による名前解決が可能

---

## 4. CORS設定の検証

### ✅ Backend CORS設定 (backend/api/app.py:72-75)

```python
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
CORS(app, origins=allowed_origins, supports_credentials=True)
logger.info(f"CORS許可オリジン: {allowed_origins}")
```

### ✅ 環境変数設定

**docker-compose.yml & docker-compose.redis.yml**:
```yaml
backend:
  environment:
    - ALLOWED_ORIGINS=http://localhost:3000,http://frontend:3000
```

**docker-compose.production.yml**:
```yaml
backend:
  environment:
    - ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
```

### ✅ 実際のリクエストフロー

```
Browser → http://localhost:3000 (Frontend)
  ↓ fetch API
Browser → http://localhost:8080/api/* (Backend)
  ↓ Origin header
Origin: http://localhost:3000 ✅
```

**検証結果**:
- ✅ ブラウザから送信されるOriginヘッダー: `http://localhost:3000`
- ✅ ALLOWED_ORIGINSに含まれている: `http://localhost:3000,http://frontend:3000`
- ✅ `http://frontend:3000` は将来のSSR対応用（現在未使用だが問題なし）
- ✅ credentials付きリクエスト対応: `supports_credentials=True`

---

## 5. サービス依存関係チェーンの検証

### ✅ docker-compose.yml

```yaml
adk:
  depends_on:
    - backend

frontend:
  depends_on:
    backend:
      condition: service_healthy
```

**起動順序**: `backend` → `adk` & `frontend`

### ✅ docker-compose.redis.yml

```yaml
backend:
  depends_on:
    - redis

adk:
  depends_on:
    - redis

frontend:
  depends_on:
    backend:
      condition: service_healthy
```

**起動順序**: `redis` → `backend` & `adk` → `frontend`

### ✅ docker-compose.production.yml

```yaml
backend:
  depends_on:
    - redis

frontend:
  depends_on:
    backend:
      condition: service_healthy
```

**起動順序**: `redis` → `backend` → `frontend`

**検証結果**:
- ✅ 依存関係が論理的に正しい
- ✅ ヘルスチェックを使用した確実な起動待機
- ✅ Redis依存サービスはRedis起動後に開始

---

## 6. ヘルスチェック設定の検証

### ✅ Backend

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/api/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### ✅ Redis

```yaml
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 10s
  timeout: 3s
  retries: 3
```

### ✅ ADK

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

**検証結果**:
- ✅ 全サービスにヘルスチェック設定済み
- ✅ start_periodが適切（Backend: 40s, ADK: 60s）
- ✅ depends_onでヘルスチェック利用

---

## 7. ポートマッピング整合性

| サービス | コンテナポート | ホストポート | アクセスURL | 状態 |
|---------|-------------|------------|------------|------|
| Backend | 8080 | 8080 | http://localhost:8080 | ✅ |
| ADK | 8000 | 8000 | http://localhost:8000 | ✅ |
| Frontend | 3000 | 3000 | http://localhost:3000 | ✅ |
| Redis | 6379 | 6379* | redis://localhost:6379 | ✅ |

\* Redis は docker-compose.redis.yml のみでホストにマッピング（デバッグ用）

**検証結果**:
- ✅ ポート衝突なし
- ✅ 標準的なポート番号使用
- ✅ 外部アクセスが必要なサービスのみマッピング

---

## 8. ボリューム共有の検証

### ✅ docker-compose.yml

```yaml
volumes:
  backend-sessions:
    driver: local

backend:
  volumes:
    - backend-sessions:/app/tmp/user_sessions

adk:
  volumes:
    - backend-sessions:/app/tmp/user_sessions  # ✅ 共有
```

**検証結果**:
- ✅ BackendとADKが同じセッションボリュームを共有
- ✅ SESSIONS_DIR環境変数が両方で一致: `/app/tmp/user_sessions`

### ✅ docker-compose.redis.yml & production.yml

```yaml
# Redisベースのセッション管理のため、ローカルボリュームは不使用
# メタデータ → Redis
# ファイル → S3/GCS (production.yml)
```

**検証結果**:
- ✅ Redis環境ではセッション共有がRedis経由で実現
- ✅ Production環境ではS3/GCSでファイル共有

---

## 9. 環境変数の一貫性

### ✅ SESSIONS_DIR

| ファイル | Backend | ADK |
|---------|---------|-----|
| docker-compose.yml | `/app/tmp/user_sessions` | `/app/tmp/user_sessions` ✅ |
| docker-compose.redis.yml | (未設定=file mode) | (未設定=file mode) ✅ |
| docker-compose.production.yml | (cloud mode, 不要) | (ADK無し) ✅ |

### ✅ SESSION_TYPE

| ファイル | 値 | 状態 |
|---------|-----|------|
| docker-compose.yml | 未設定 (デフォルト: file) | ✅ |
| docker-compose.redis.yml | `redis` | ✅ |
| docker-compose.production.yml | 未設定 (cloud mode) | ✅ |

### ✅ STORAGE_MODE

| ファイル | 値 | 状態 |
|---------|-----|------|
| docker-compose.yml | 未設定 (デフォルト: local) | ✅ |
| docker-compose.redis.yml | 未設定 (デフォルト: local) | ✅ |
| docker-compose.production.yml | `cloud` | ✅ |

**検証結果**:
- ✅ 各環境で適切なストレージモード選択
- ✅ 環境変数の命名規則統一

---

## 10. 潜在的な問題点と推奨事項

### ⚠️ 注意点 1: Production環境のNEXT_PUBLIC_API_URL

**現状**:
```yaml
# docker-compose.production.yml
frontend:
  environment:
    - NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
```

**推奨**:
実際のデプロイ時には、.envファイルまたはCI/CDで以下を設定:
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### ⚠️ 注意点 2: ADK開発UIの本番環境

**現状**: `docker-compose.production.yml` にADKサービスが含まれていない

**理由**: ADKは開発ツールであり、本番環境では不要（正しい設計）

**推奨**: 現状維持でOK

### ⚠️ 注意点 3: Redisポートのホスト公開

**現状**: `docker-compose.redis.yml` でRedisポート6379を公開

```yaml
redis:
  ports:
    - "6379:6379"  # ⚠️ デバッグ用
```

**推奨**:
- ローカル開発・デバッグ時のみ公開
- Production環境では削除推奨（docker-compose.production.ymlでは未公開 ✅）

### ✅ 良い点 1: ヘルスチェックベースの依存関係

```yaml
frontend:
  depends_on:
    backend:
      condition: service_healthy  # ✅ 確実な起動待機
```

### ✅ 良い点 2: 環境別のdocker-composeファイル分離

- `docker-compose.yml` - ローカル開発
- `docker-compose.redis.yml` - Redisテスト
- `docker-compose.production.yml` - 本番環境

分離により、誤って開発設定で本番デプロイするリスクが低減 ✅

---

## 11. 接続テスト推奨コマンド

### ローカル開発環境 (docker-compose.yml)

```bash
# 1. 起動
docker-compose up -d

# 2. ネットワーク確認
docker network inspect hera-network

# 3. Backend疎通確認
curl http://localhost:8080/api/health

# 4. Frontend疎通確認
curl http://localhost:3000

# 5. ADK疎通確認
curl http://localhost:8000

# 6. コンテナ間通信確認（backend → adk）
docker exec hera-backend curl -f http://adk:8000
```

### Redis環境 (docker-compose.redis.yml)

```bash
# 1. 起動
docker-compose -f docker-compose.redis.yml up -d

# 2. Redis接続確認（Backendから）
docker exec hera-backend redis-cli -h redis ping
# 期待出力: PONG

# 3. Redis接続確認（ADKから）
docker exec hera-adk redis-cli -h redis ping
# 期待出力: PONG

# 4. セッションデータ確認
docker exec hera-redis redis-cli KEYS "session:*"
```

### Production環境 (docker-compose.production.yml)

```bash
# 1. 起動（環境変数必須）
NEXT_PUBLIC_API_URL=http://localhost:8080 \
ALLOWED_ORIGINS=http://localhost:3000 \
S3_BUCKET_NAME=your-bucket \
AWS_ACCESS_KEY_ID=xxx \
AWS_SECRET_ACCESS_KEY=xxx \
docker-compose -f docker-compose.production.yml up -d

# 2. Redis接続確認
docker exec hera-backend redis-cli -h redis ping

# 3. S3接続確認（Backendログで確認）
docker logs hera-backend | grep -i s3
```

---

## 12. 結論

### ✅ 総合評価: **合格**

すべてのコンテナ間接続設定は正しく構成されており、以下の点が確認されました:

1. ✅ **Redis接続**: サービス名とURL一致、全サービスが正しく接続
2. ✅ **Frontend↔Backend**: ポートマッピングとCORS設定が適切
3. ✅ **ネットワーク構成**: 全サービスが同一bridgeネットワークで接続
4. ✅ **依存関係**: 論理的に正しい起動順序
5. ✅ **ヘルスチェック**: 確実なサービス起動待機
6. ✅ **ボリューム共有**: BackendとADK間でセッションデータ共有
7. ✅ **環境変数**: 一貫性のある命名規則と設定

### 推奨アクション

1. **現状維持**: コンテナネットワーク設定は変更不要
2. **本番デプロイ時**: `NEXT_PUBLIC_API_URL` と `ALLOWED_ORIGINS` を実際のドメインに設定
3. **セキュリティ**: 本番環境ではRedisポートを公開しない（現在の設計で正しい）

---

**検証者**: Claude
**検証完了日**: 2025-10-28
