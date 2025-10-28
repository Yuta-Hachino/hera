# 🚀 クラウドデプロイメントガイド

## 📋 目次

1. [環境別の推奨構成](#環境別の推奨構成)
2. [AWS へのデプロイ](#aws-へのデプロイ)
3. [GCP へのデプロイ](#gcp-へのデプロイ)
4. [セッションデータとファイル管理](#セッションデータとファイル管理)
5. [コスト最適化](#コスト最適化)

---

## 環境別の推奨構成

### 🏠 ローカル開発環境

```bash
# ファイルベースのストレージ（シンプル）
docker-compose up
```

**特徴**:
- ✅ セットアップが簡単
- ✅ 追加コスト不要
- ❌ 本番環境では使用不可

**設定**:
```env
STORAGE_MODE=local
SESSIONS_DIR=./tmp/user_sessions
```

---

### 🧪 ステージング環境

```bash
# Redis + ローカルストレージ（コスト抑制）
docker-compose -f docker-compose.yml -f docker-compose.redis.yml up
```

**特徴**:
- ✅ 本番に近い環境
- ✅ コストを抑えられる
- ⚠️ ファイルの永続性に注意

**設定**:
```env
STORAGE_MODE=local
SESSION_TYPE=redis
REDIS_URL=redis://redis:6379/0
```

---

### 🏭 本番環境（推奨）

```bash
# Redis + S3/GCS（スケーラブル）
docker-compose -f docker-compose.yml -f docker-compose.production.yml up
```

**特徴**:
- ✅ 高可用性
- ✅ スケーラブル
- ✅ コスト効率が良い
- ✅ マルチリージョン対応

**設定**:
```env
# ストレージ設定
STORAGE_MODE=cloud
CLOUD_STORAGE_TYPE=s3  # または gcs, azure

# Redis（メタデータ）
REDIS_URL=redis://your-redis-url:6379/0

# AWS S3（画像ファイル）
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=ap-northeast-1
S3_BUCKET_NAME=your-bucket-name
```

---

## AWS へのデプロイ

### 1️⃣ 必要なリソースの作成

#### S3バケット

```bash
# S3バケットを作成
aws s3 mb s3://hera-sessions-prod --region ap-northeast-1

# CORSを設定
aws s3api put-bucket-cors --bucket hera-sessions-prod --cors-configuration file://cors.json
```

**cors.json**:
```json
{
  "CORSRules": [
    {
      "AllowedOrigins": ["https://yourdomain.com"],
      "AllowedMethods": ["GET", "PUT", "POST"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 3000
    }
  ]
}
```

#### ElastiCache (Redis)

```bash
# Redisクラスターを作成
aws elasticache create-cache-cluster \
  --cache-cluster-id hera-redis-prod \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1
```

### 2️⃣ IAMポリシーの設定

**推奨ポリシー**（最小権限の原則）:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::hera-sessions-prod/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::hera-sessions-prod"
    }
  ]
}
```

### 3️⃣ ECS/Fargate デプロイ

**task-definition.json**:
```json
{
  "family": "hera-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-ecr-repo/hera-backend:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "STORAGE_MODE", "value": "cloud"},
        {"name": "CLOUD_STORAGE_TYPE", "value": "s3"},
        {"name": "S3_BUCKET_NAME", "value": "hera-sessions-prod"},
        {"name": "AWS_REGION", "value": "ap-northeast-1"}
      ],
      "secrets": [
        {"name": "GEMINI_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "REDIS_URL", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/hera-backend",
          "awslogs-region": "ap-northeast-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

---

## GCP へのデプロイ

### 1️⃣ Google Cloud Storage

```bash
# バケットを作成
gsutil mb -l asia-northeast1 gs://hera-sessions-prod

# CORSを設定
gsutil cors set cors.json gs://hera-sessions-prod
```

### 2️⃣ Cloud Memorystore (Redis)

```bash
# Redisインスタンスを作成
gcloud redis instances create hera-redis-prod \
  --size=1 \
  --region=asia-northeast1 \
  --redis-version=redis_7_0
```

### 3️⃣ Cloud Run デプロイ

```bash
# コンテナをビルド
gcloud builds submit --tag gcr.io/your-project/hera-backend

# Cloud Runにデプロイ
gcloud run deploy hera-backend \
  --image gcr.io/your-project/hera-backend \
  --platform managed \
  --region asia-northeast1 \
  --set-env-vars="STORAGE_MODE=cloud,CLOUD_STORAGE_TYPE=gcs,GCS_BUCKET_NAME=hera-sessions-prod" \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest,REDIS_URL=redis-url:latest"
```

---

## セッションデータとファイル管理

### 🗂️ データ構造

```
セッション: abc123
├── メタデータ (Redis)
│   ├── session:abc123:meta:user_profile → {"age": 30, ...}
│   ├── session:abc123:meta:conversation → [...]
│   └── session:abc123:meta:file:photos/user.png → {"url": "https://..."}
│
└── ファイル (S3/GCS)
    ├── sessions/abc123/photos/user.png
    ├── sessions/abc123/photos/partner.png
    └── sessions/abc123/photos/child_1.png
```

### 🔄 データフロー

```
ユーザー
  │
  ↓ 画像アップロード
Backend API
  │
  ├─→ メタデータ保存 → Redis
  │    (session_id, ファイル名, サイズ, etc.)
  │
  └─→ 画像ファイル保存 → S3/GCS
       (実ファイル)

ADK/Backend
  │
  ├─→ メタデータ取得 ← Redis
  │    (URLを取得)
  │
  └─→ 画像URL生成 or ダウンロード ← S3/GCS
```

### 💾 ライフサイクル管理

#### Redis の TTL 設定

```python
# 24時間でメタデータが自動削除される
REDIS_URL=redis://...
SESSION_TTL=86400  # 秒
```

#### S3 の Lifecycle Policy

```json
{
  "Rules": [
    {
      "Id": "DeleteOldSessions",
      "Status": "Enabled",
      "Prefix": "sessions/",
      "Expiration": {
        "Days": 7
      }
    }
  ]
}
```

```bash
# ライフサイクルポリシーを適用
aws s3api put-bucket-lifecycle-configuration \
  --bucket hera-sessions-prod \
  --lifecycle-configuration file://lifecycle.json
```

---

## コスト最適化

### 💡 推奨設定

#### 1. Redis のメモリ最適化

```yaml
# docker-compose.production.yml
redis:
  command: >
    redis-server
    --maxmemory 256mb
    --maxmemory-policy allkeys-lru  # 古いキーを自動削除
    --save ""  # RDB永続化を無効化（高速化）
```

#### 2. S3 ストレージクラスの選択

| クラス | 用途 | コスト | 取り出し速度 |
|--------|------|--------|-------------|
| **Standard** | 頻繁アクセス | 高 | 即座 |
| **Standard-IA** | 稀にアクセス | 中 | やや遅い |
| **Glacier** | アーカイブ | 低 | 遅い |

**推奨**:
- 新規セッション（7日以内）: **Standard**
- 古いセッション（7日以降）: **Standard-IA**（Lifecycleで自動移行）

#### 3. CDN の活用

```
ユーザー
  ↓
CloudFront / Cloud CDN
  ↓ (キャッシュミス時のみ)
S3 / GCS
```

**メリット**:
- 画像の読み込みが高速化
- S3/GCS の転送コスト削減
- グローバルなユーザーにも対応

---

## 📊 月間コスト試算

### 想定条件
- アクティブユーザー: 1,000人/月
- セッションあたりデータ: 1.5MB (JSON 10KB + 画像 1.5MB)
- リージョン: 東京 (ap-northeast-1)

### AWS構成

| リソース | 仕様 | 月額コスト |
|---------|------|-----------|
| ElastiCache (Redis) | cache.t3.micro (0.5GB) | $12 |
| S3 Standard | 1.5GB ストレージ | $0.03 |
| S3 データ転送 | 10GB/月 | $0.90 |
| ECS Fargate | 0.5 vCPU, 1GB メモリ | $15 |
| **合計** | - | **約 $28/月** |

### GCP構成

| リソース | 仕様 | 月額コスト |
|---------|------|-----------|
| Memorystore (Redis) | Basic 1GB | $30 |
| Cloud Storage | 1.5GB | $0.02 |
| Cloud Run | 512MB メモリ | $10 |
| **合計** | - | **約 $40/月** |

---

## 🔒 セキュリティベストプラクティス

### 1. 環境変数の管理

❌ **NG**: コードに直接記述
```python
AWS_ACCESS_KEY_ID = "AKIA..."  # 絶対ダメ！
```

✅ **OK**: Secrets Manager を使用
```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name hera/gemini-api-key \
  --secret-string "your-api-key"

# GCP Secret Manager
gcloud secrets create gemini-api-key \
  --data-file=-
```

### 2. S3 バケットポリシー

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": "arn:aws:s3:::hera-sessions-prod/*",
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

### 3. ネットワーク分離

```
Internet
  ↓
ALB / Load Balancer (Public Subnet)
  ↓
ECS / Cloud Run (Private Subnet)
  ↓
Redis / RDS (Private Subnet)
  ↓
S3 / GCS (VPC Endpoint経由)
```

---

## 🆘 トラブルシューティング

### Redis接続エラー

```bash
# 接続確認
redis-cli -h your-redis-endpoint ping

# パスワード付きの場合
redis-cli -h your-redis-endpoint -a your-password ping
```

### S3アクセスエラー

```bash
# IAMロールの確認
aws sts get-caller-identity

# バケットへのアクセステスト
aws s3 ls s3://hera-sessions-prod/
```

### メモリ不足エラー

```bash
# Redisメモリ使用量確認
redis-cli info memory

# 使用量が多い場合はTTLを短縮
redis-cli config set maxmemory-policy allkeys-lru
```

---

## 📚 参考リンク

- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)
- [S3 Performance Optimization](https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html)
