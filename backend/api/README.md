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
python test_full_flow.py
```

### 2. 個別APIテスト

#### セッション作成
```bash
curl -X POST http://localhost:8080/api/sessions
```

#### メッセージ送信
```bash
curl -X POST http://localhost:8080/api/sessions/{session_id}/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "こんにちは、33歳のエンジニアです"}'
```

#### セッション状態確認
```bash
curl http://localhost:8080/api/sessions/{session_id}/status
```

#### セッション完了
```bash
curl -X POST http://localhost:8080/api/sessions/{session_id}/complete
```

#### 画像アップロード
```bash
curl -X POST http://localhost:8080/api/sessions/{session_id}/photos/user \
  -F "file=@dummy_user.png"
```

#### 画像生成
```bash
curl -X POST http://localhost:8080/api/sessions/{session_id}/generate-image \
  -H "Content-Type: application/json" \
  -d '{"type": "partner", "description": "明るくて優しい人"}'
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
