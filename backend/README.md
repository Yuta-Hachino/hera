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
# セッションデータの保存先（オプション、デフォルト: backend/tmp/user_sessions）
# SESSIONS_DIR=tmp/user_sessions
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
- `GET /api/health` - ヘルスチェック
- `POST /api/sessions` - セッション作成
- `POST /api/sessions/{session_id}/messages` - メッセージ送信
- `POST /api/sessions/{session_id}/photos/{type}` - 画像アップロード
- `POST /api/sessions/{session_id}/generate-image` - 画像生成

## 🧪 テスト実行

### フルフローテスト
```bash
cd backend
python test_full_flow.py
```

### 自動テストスクリプト
```bash
cd backend
./run_test.sh
```

詳細なテスト情報は [API README](api/README.md) を参照してください。

## 📚 ドキュメント

- [家族エージェント設計](../docs/FAMILY_AGENT_DESIGN.md)
- [ストーリー生成仕様](../docs/STORY_GENERATION.md)
- [手紙生成仕様](../docs/LETTER_GENERATION.md)

## 🖼️ 画像アップロード・生成API（追加機能・設計）

### 1. ユーザー画像アップロード
- エンドポイント: `POST /api/sessions/{session_id}/photos/user`
- Content-Type: multipart/form-data
- サーバー保存先：`photos/user.png`

### 2. パートナー画像生成（Geminiベース）
- エンドポイント: `POST /api/sessions/{session_id}/generate-image`
- リクエスト例:
```json
{
  "target": "partner"
}
```
- サーバーが`partner_face_description`をプロンプトにGeminiで画像生成
- 保存: `photos/partner.png`

### 3. 子ども画像合成（拡張予定）
- エンドポイント: `POST /api/sessions/{session_id}/generate-child-image`
- user/partner両画像からAI合成
- 保存例: `photos/child_1.png`

### 4. 保存ルール
- `photos/user.png`: ユーザー本人画像
- `photos/partner.png`: パートナー画像
- `photos/child_{N}.png`: 子ども画像

### 5. エラーハンドリングと挙動メモ
- アップロードや生成素材が未登録の場合はエラー返却
- 画像URL＋metaを返す