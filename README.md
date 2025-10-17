# AIハッカソン - マルチエージェントアプリケーション

LangGraphを使用したマルチエージェントシステムのデモアプリケーション。

## 技術スタック

- **フロントエンド**: Next.js 15 + React 19 + TypeScript + Tailwind CSS
- **バックエンド**: Python 3.11 + FastAPI + LangGraph + OpenAI API
- **インフラ**: Docker Compose

## 主な機能

### マルチエージェントシステム

4つの専門エージェントが協調動作：

1. **Router Agent** - 質問を分析しWeb検索の要否を判定
2. **Researcher Agent** - Perplexity APIでWeb検索を実行
3. **Analyzer Agent** - 収集した情報を分析
4. **Composer Agent** - 最終回答を生成

### ワークフロー

```
ユーザー入力
    ↓
Router Agent → 検索が必要？
    ↓ Yes                    ↓ No
Researcher Agent          Composer Agent
    ↓                          ↓
Analyzer Agent              回答生成
    ↓
Composer Agent
    ↓
ユーザーへ出力
```

## セットアップ

### 前提条件

- Docker Desktop
- OpenAI API キー
- Perplexity API キー（オプション）

### 環境変数の設定

`.env.sample`をコピーして`.env`を作成し、APIキーを設定：

```bash
cp .env.sample .env
```

`.env`ファイルを編集：

```bash
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4.1-mini
PERPLEXITY_API_KEY=pplx-your-key-here
```

### 起動方法

開発環境（ホットリロード有効）：

```bash
make serve-dev
```

本番環境：

```bash
make serve-prod
```

### アクセスURL

- **フロントエンド**: http://localhost:3000
- **バックエンドAPI**: http://localhost:8002
- **API ドキュメント**: http://localhost:8002/docs

### 停止方法

```bash
make down-dev    # 開発環境
make down-prod   # 本番環境
```

## その他のコマンド

```bash
make help        # ヘルプを表示
make logs-dev    # ログ確認
make clean       # すべてクリーンアップ
```

詳細は [DEVELOPMENT.md](./DEVELOPMENT.md) を参照してください。

## ディレクトリ構成

```
.
├── backend/                  # Python バックエンド
│   ├── app/
│   │   ├── agents/          # LangGraphエージェント
│   │   ├── api/            # FastAPI ルート
│   │   ├── models/         # データモデル
│   │   ├── services/       # ビジネスロジック
│   │   └── main.py         # エントリーポイント
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                 # Next.js フロントエンド
│   ├── app/                 # App Router
│   ├── components/          # React コンポーネント
│   ├── Dockerfile
│   └── package.json
│
├── docker-compose.dev.yaml   # 開発環境設定
├── docker-compose.prod.yaml  # 本番環境設定
├── Makefile                  # よく使うコマンドをまとめています。
└── .env                      # 環境変数
```
