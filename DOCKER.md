# 🐳 Docker セットアップガイド

このドキュメントでは、AIファミリー・シミュレーターをDockerで実行する方法を説明します。

## 📋 前提条件

- Docker 20.10以降
- Docker Compose 2.0以降
- Google Gemini APIキー（https://aistudio.google.com/app/apikey で取得）

## 🚀 クイックスタート

### 1. 環境変数の設定

プロジェクトルートに `.env` ファイルを作成します：

```bash
# .envファイルを作成
cp backend/.env.example .env

# .envファイルを編集してAPIキーを設定
# 必須: GEMINI_API_KEY=your-actual-api-key-here
```

### 2. Dockerコンテナの起動

```bash
# 全サービスをビルドして起動
docker-compose up --build

# バックグラウンドで起動する場合
docker-compose up -d --build
```

### 3. アクセス

サービスが起動したら、以下のURLにアクセスできます：

- **フロントエンド**: http://localhost:3000
- **バックエンドAPI**: http://localhost:8080
- **Google ADK開発UI**: http://localhost:8000

### 4. 停止

```bash
# コンテナを停止
docker-compose down

# ボリュームも削除する場合
docker-compose down -v
```

## 📦 サービス構成

### バックエンドAPI (Flask)
- **ポート**: 8080
- **Dockerfile**: `backend/Dockerfile`
- **ヘルスチェック**: `/api/health`
- **機能**:
  - セッション管理
  - ユーザー情報収集
  - AI応答生成

### Google ADK開発UI
- **ポート**: 8000
- **機能**:
  - エージェントのテストと開発
  - リアルタイムデバッグ

### フロントエンド (Next.js)
- **ポート**: 3000
- **Dockerfile**: `frontend/Dockerfile`
- **ビルド方式**: Standalone
- **機能**:
  - ユーザーインターフェース
  - Live2Dアバター表示
  - チャット機能

## 🔧 開発モード

### ホットリロードの有効化

開発時は、ソースコードの変更を即座に反映できます：

```yaml
# docker-compose.override.yml を作成
version: '3.8'

services:
  backend:
    volumes:
      - ./backend:/app  # :ro を削除してread-writeにする
    environment:
      - FLASK_DEBUG=True
      - LOG_LEVEL=DEBUG

  frontend:
    command: npm run dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
```

```bash
# 開発モードで起動
docker-compose -f docker-compose.yml -f docker-compose.override.yml up
```

### ログの確認

```bash
# 全サービスのログを表示
docker-compose logs -f

# 特定のサービスのログを表示
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f adk
```

## 🧪 テストの実行

### バックエンドのテスト

```bash
# コンテナ内でテストを実行
docker-compose exec backend pytest

# カバレッジ付きでテスト
docker-compose exec backend pytest --cov=. --cov-report=html

# 特定のテストファイルを実行
docker-compose exec backend pytest tests/test_env_validator.py
```

## 🐛 トラブルシューティング

### ポートが既に使用されている

```bash
# 使用中のポートを確認
lsof -i :3000
lsof -i :8080
lsof -i :8000

# ポート番号を変更する場合（docker-compose.ymlを編集）
services:
  frontend:
    ports:
      - "3001:3000"  # 3001に変更
```

### ビルドエラーが発生する

```bash
# キャッシュをクリアして再ビルド
docker-compose build --no-cache

# すべてのコンテナとイメージを削除して再起動
docker-compose down -v
docker system prune -a
docker-compose up --build
```

### 環境変数が反映されない

```bash
# .envファイルの確認
cat .env

# コンテナの環境変数を確認
docker-compose exec backend env | grep GEMINI
```

### セッションデータが消える

セッションデータはDockerボリュームに永続化されています：

```bash
# ボリュームの確認
docker volume ls | grep hera

# ボリュームの詳細情報
docker volume inspect hera_backend-sessions

# ボリュームのバックアップ
docker run --rm -v hera_backend-sessions:/data -v $(pwd):/backup alpine \
  tar czf /backup/sessions-backup.tar.gz /data
```

## 📊 リソース使用量の監視

```bash
# コンテナのリソース使用状況を確認
docker stats

# 特定のコンテナの情報
docker inspect hera-backend
docker inspect hera-frontend
docker inspect hera-adk
```

## 🔒 本番環境への移行

### セキュリティ設定

1. **環境変数の管理**
   ```bash
   # .envファイルをGitから除外（既に.gitignoreに含まれています）
   echo ".env" >> .gitignore
   ```

2. **デバッグモードの無効化**
   ```bash
   # .envファイル
   FLASK_DEBUG=False
   LOG_LEVEL=INFO
   ```

3. **CORS設定の制限**
   ```bash
   # .envファイル
   ALLOWED_ORIGINS=https://yourdomain.com
   ```

### パフォーマンス最適化

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  frontend:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

```bash
# 本番モードで起動
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📝 よくある質問

### Q: ADKが起動しない
A: ADKの起動には時間がかかる場合があります。以下を確認してください：
```bash
# ADKのログを確認
docker-compose logs -f adk

# GEMINI_API_KEYが設定されているか確認
docker-compose exec adk env | grep GEMINI_API_KEY
```

### Q: フロントエンドがバックエンドに接続できない
A: NEXT_PUBLIC_API_URLが正しく設定されているか確認してください：
```bash
# 環境変数の確認
docker-compose exec frontend env | grep NEXT_PUBLIC_API_URL

# ネットワークの確認
docker network inspect hera_hera-network
```

### Q: データベースは必要ですか？
A: いいえ、現在のバージョンではファイルベースのセッション管理を使用しているため、データベースは不要です。

## 🤝 貢献

バグ報告や機能要望は、GitHubのIssueまでお願いします。

## 📄 ライセンス

このプロジェクトのライセンスについては、LICENSEファイルを参照してください。
