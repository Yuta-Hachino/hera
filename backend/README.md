# Backend - Hera AI Family Simulator

AIファミリー・シミュレーターのバックエンドシステムです。

## 📁 ディレクトリ構成

```
backend/
├── agents/           # Google ADKエージェント
│   ├── hera/        # Heraエージェント（プロファイル収集）
│   └── family/      # 家族エージェント（マルチエージェント会話）
├── api/             # Flask API（将来のフロントエンド連携用）
├── tmp/             # セッションデータ
├── tests/           # テストファイル
└── requirements.txt # 依存関係
```

## 🚀 セットアップ

### 1. 仮想環境の作成と有効化

```bash
# プロジェクトルートで実行
python3 -m venv .venv

# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 2. 依存関係のインストール

```bash
# プロジェクトルートから
pip install -r backend/requirements.txt
```

### 3. 環境変数の設定

`backend/.env` ファイルを作成:

```bash
cd backend
cp env.example .env
# .envファイルを編集して以下を設定
```

```.env
GOOGLE_API_KEY=your_gemini_api_key_here
FAMILY_SESSIONS_DIR=./tmp/user_sessions
```

## 🎯 使い方

### ADKエージェントの起動（メイン機能）

```bash
# backendディレクトリに移動
cd backend

# ADK Web UIを起動（agentsディレクトリを指定）
adk web agents
```

ブラウザで http://localhost:8000 にアクセス

#### 利用可能なエージェント

**1. hera_session_agent** - Heraエージェント（プロファイル収集）
   - ユーザーの基本情報を会話で収集
   - Big Five性格特性の分析
   - パートナー情報の収集

**2. family_session_agent** - 家族エージェント（家族会話）
   - 未来の家族メンバーとの会話
   - 旅行計画などの日常会話
   - 会話終了後、自動でストーリーと手紙を生成

### 生成されたコンテンツの確認

```bash
backend/tmp/user_sessions/<session_id>/family_plan.json
```

## 🔌 Flask API（将来のフロントエンド連携用）

```bash
cd backend/api
python app.py
```

エンドポイント:
- `GET /v1/health` - ヘルスチェック
- `POST /v1/simulate` - 家族シミュレーション（雛形）

## 📚 ドキュメント

- [家族エージェント設計](../docs/FAMILY_AGENT_DESIGN.md)
- [ストーリー生成仕様](../docs/STORY_GENERATION.md)
- [手紙生成仕様](../docs/LETTER_GENERATION.md)
