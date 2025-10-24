# API テスト実行ガイド

## 概要

このAPIは、Heraエージェントとの会話から家族フェーズまで一貫したテストを実行するためのFlaskアプリケーションです。

## 前提条件

### 1. 必要なサービス
- **ADK Web UI**: `http://localhost:8000` で起動している必要があります
- **Python仮想環境**: `.venv` がアクティブになっている必要があります
- **必要な環境変数**: `GEMINI_API_KEY` が設定されている必要があります

### 2. 依存関係のインストール
```bash
# 仮想環境をアクティブ化
source .venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt
```

## 起動方法

### 1. APIサーバーの起動
```bash
# プロジェクトルートから
source .venv/bin/activate
cd backend
python api/app.py
```

APIサーバーは `http://localhost:8080` で起動します。

### 2. ADK Web UIの起動
別のターミナルで以下を実行：
```bash
# ADK Web UIを起動（別途設定が必要）
# 通常は http://localhost:8000 で起動
```

## テスト実行

### 1. フルフローテストの実行
```bash
# プロジェクトルートから
cd backend
python3 tests/test_full_flow.py
```

### 2. 手動APIテスト（推奨）

#### 前提条件
- APIサーバーが起動していること（`python3 api/app.py`）
- ADK Web UIが起動していること（`adk web agents`）

#### Step 1: ヘルスチェック
```bash
curl -s http://localhost:8080/api/health
```
**期待結果**: `{"status": "ok"}`

#### Step 2: セッション作成
```bash
curl -X POST http://localhost:8080/api/sessions
```
**期待結果**: セッションIDが返される
```json
{
  "session_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "status": "created",
  "created_at": "2025-01-21T10:00:00Z"
}
```

#### Step 3: メッセージ送信（Heraエージェントとの会話）
```bash
# メッセージ1: 自己紹介
curl -X POST http://localhost:8080/api/sessions/{SESSION_ID}/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "こんにちは、33歳のエンジニアです"}'

# メッセージ2: 居住地・状況
curl -X POST http://localhost:8080/api/sessions/{SESSION_ID}/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "独身で、東京に住んでいます"}'

# メッセージ3: 理想のパートナー
curl -X POST http://localhost:8080/api/sessions/{SESSION_ID}/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "理想のパートナーは明るくて優しい人です"}'

# メッセージ4: パートナーの特徴
curl -X POST http://localhost:8080/api/sessions/{SESSION_ID}/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "パートナーの顔の特徴は、目が大きくて笑顔が素敵な人です"}'

# メッセージ5: 自分の性格
curl -X POST http://localhost:8080/api/sessions/{SESSION_ID}/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "私の性格は社交的で新しいことが好きです"}'

# メッセージ6: 子どもの希望
curl -X POST http://localhost:8080/api/sessions/{SESSION_ID}/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "将来は女の子1人と男の子1人を希望しています"}'
```

**注意**: `{SESSION_ID}` はStep 2で取得したセッションIDに置き換えてください。

#### Step 4: セッション状態確認
```bash
curl -s http://localhost:8080/api/sessions/{SESSION_ID}/status
```
**期待結果**: 会話履歴とプロファイル情報が表示される

#### Step 5: セッション完了
```bash
curl -X POST http://localhost:8080/api/sessions/{SESSION_ID}/complete
```
**期待結果**: セッション完了のメッセージが返される

#### Step 6: 画像処理（オプション）
```bash
# ユーザー画像アップロード
curl -X POST http://localhost:8080/api/sessions/{SESSION_ID}/photos/user \
  -F "file=@api/dummy_user.png"

# パートナー画像生成
curl -X POST http://localhost:8080/api/sessions/{SESSION_ID}/generate-image \
  -H "Content-Type: application/json" \
  -d '{"type": "partner", "description": "明るくて優しい人"}'

# 子ども画像生成
curl -X POST http://localhost:8080/api/sessions/{SESSION_ID}/generate-child-image \
  -H "Content-Type: application/json" \
  -d '{"type": "child", "description": "両親の特徴を組み合わせた子ども"}'
```

### 3. 自動テストスクリプト
```bash
cd backend
./tests/run_test.sh
```

### 4. レスポンスの見やすくする方法

#### JSONを整形して表示
```bash
curl -X POST http://localhost:8080/api/sessions/{SESSION_ID}/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "テスト"}' | python3 -m json.tool
```

#### 日本語メッセージのみを抽出
```bash
curl -X POST http://localhost:8080/api/sessions/{SESSION_ID}/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "テスト"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['reply'])"
```

## API エンドポイント

### 1. セッション管理
- `POST /api/sessions` - セッション作成
- `GET /api/sessions/{session_id}/status` - セッション状態取得
- `POST /api/sessions/{session_id}/complete` - セッション完了

### 2. メッセージ処理
- `POST /api/sessions/{session_id}/messages` - メッセージ送信

### 3. 画像処理
- `POST /api/sessions/{session_id}/photos/{type}` - 画像アップロード
- `POST /api/sessions/{session_id}/generate-image` - 画像生成
- `POST /api/sessions/{session_id}/generate-child-image` - 子ども画像生成

### 4. ヘルスチェック
- `GET /api/health` - API状態確認

## テストフロー

1. **セッション作成**: 新しいセッションIDを生成
2. **メッセージ送信**: Heraエージェントとの会話（6回のメッセージ）
3. **セッション状態確認**: プロファイルと進捗の確認
4. **セッション完了**: 情報収集の完了処理
5. **画像処理**: ユーザー画像のアップロードと生成
6. **最終状態確認**: セッションの最終状態を確認

## データ保存

セッションデータは以下の場所に保存されます：
```
backend/tmp/user_sessions/{session_id}/
├── user_profile.json          # ユーザープロファイル
├── conversation_history.json   # 会話履歴
└── photos/                    # アップロードされた画像
    └── user.png
```

## トラブルシューティング

### 1. よくあるエラー

#### ADK Web UI接続エラー
```
エージェント通信エラー: 404 Client Error: Not Found
```
**解決方法**: ADK Web UIが起動していることを確認

#### セッション作成エラー
```
セッション作成エラー: 409
```
**解決方法**: 同じセッションIDが既に存在する場合、新しいセッションIDを使用

#### 画像生成エラー
```
画像生成失敗: 400
```
**解決方法**: Gemini APIキーが正しく設定されていることを確認

### 2. ログの確認

APIサーバーのログを確認するには、起動時のターミナル出力を確認してください。

### 3. デバッグモード

APIサーバーはデバッグモードで起動しているため、エラーの詳細な情報が表示されます。

## 注意事項

- ADK Web UIとAPIサーバーは別々のプロセスで起動する必要があります
- テスト実行前に、両方のサービスが正常に起動していることを確認してください
- 画像生成には有効なGemini APIキーが必要です
- セッションデータはファイルベースで保存されるため、サーバー再起動後も保持されます

