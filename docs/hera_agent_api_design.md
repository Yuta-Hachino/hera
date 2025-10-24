# Heraエージェント API設計ドキュメント（リニューアル版: 2025/10/24）

## 概要

本システムは、Google ADK/Gemini連携のHera（家族観・価値観ヒアリングAI）をFlaskベースREST APIサーバーで提供します。

- **REST API**: Flask（8080ポート）
- **永続化**: セッションごとにJSONファイル永続化
- **セッション管理**: APIから新規/更新/完了、進捗取得
- **Hera Family Agent**: 情報収集からファミリー連携まで一貫制御

---

## エンドポイント一覧・役割

- **POST /api/sessions**: ユーザーごとの新規セッション生成（UUID払い出し）
- **POST /api/sessions/{session_id}/messages**: ユーザー発話を送信、情報抽出LLM & エージェント返答
- **GET /api/sessions/{session_id}/status**: 収集済みプロフィール・履歴・進捗取得
- **POST /api/sessions/{session_id}/complete**: 必須情報揃ったら完了・Family Agent側に転送
- **GET /api/health**: サーバーヘルス

### 主要実体
- user_profile: 各セッションの構造化ユーザープロファイル
- conversation_history: 全発話履歴リスト
- information_progress: 必須項目ごとの収集進捗（論理名:bool）

---

## 代表的APIリクエスト/レスポンス例（curl形式）

```bash
# セッション作成
curl -X POST http://localhost:8080/api/sessions

# 発話送信
curl -X POST http://localhost:8080/api/sessions/{session_id}/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "こんにちは、33歳のエンジニアです"}'

# 進捗・状態確認
curl http://localhost:8080/api/sessions/{session_id}/status
```

（※詳細なschema例や構造は従来通り継続記載）

---

### ✔️ 新API: 画像アップロード・生成・合成

#### 1. ユーザー画像アップロード
`POST /api/sessions/{session_id}/photos/user`
- multipart/form-data
- フロントから画像アップロード、`photos/user.png`に保存

#### 2. パートナー画像生成
`POST /api/sessions/{session_id}/generate-image`
- JSON: `{ "target": "partner" }`
- `partner_face_description`をGemini APIプロンプトに変換→生成→`photos/partner.png`

#### 3. 子ども画像合成（拡張予定）
`POST /api/sessions/{session_id}/generate-child-image`
- `photos/user.png`と`photos/partner.png`が必須
- 顔合成アルゴリズムで生成し`photos/child_1.png`等に保存

#### 保存ファイル例
- `photos/user.png`: アップロード画像
- `photos/partner.png`: Gemini生成画像
- `photos/child_1.png`: 合成画像

#### レスポンス例
```json
{
  "status": "success",
  "image_url": "/api/sessions/xxxx/photos/partner.png",
  "meta": { "target": "partner", ... }
}
```

#### エラー
- 入力画像/材料の未登録などで失敗時は `status: error` とエラー理由返却

---

## ディレクトリと主要コンポーネント

- `backend/agents/hera/`
  - `adk_hera_agent.py`: Heraエージェント（ADK・Geminiベース、抽出/ヒアリング主担当）
  - `root_agent.py`: エージェントエントリポイント
- `backend/agents/family/`: Family Agent関連
- `backend/api/`: FlaskによるAPI実装（将来的なREST/HTTP定義で利用）
- `backend/tmp/user_sessions/`: プロファイル・履歴・生成物保存

---

## API設計・やりとり概要

### 1. セッションの作成

**POST /api/sessions**
- ユーザーごとの新規セッション生成
- レスポンス例:
```json
{
  "session_id": "abc-123",
  "created_at": "2025-10-22T12:01:23",
  "status": "created"
}
```

---

### 2. メッセージ送信（情報抽出＆会話進行）

**POST /api/sessions/{session_id}/messages**
- ユーザー発話を送信、LLMとHeraエージェントが情報抽出＆応答
- 必須・推奨・補完フィールドを進捗管理
- レスポンス例:
```json
{
  "reply": "ありがとうございます。年齢とパートナーの有無を教えていただけますか？",
  "conversation_history": [
    {"speaker": "user", "message": "33歳独身 東京です"},
    {"speaker": "hera", "message": "ありがとうございます..."}
  ],
  "user_profile": {
    "age": 33,
    "relationship_status": "single",
    "location": "東京"
  },
  "information_progress": {
    "age": true,
    "relationship_status": true,
    "user_personality_traits": false,
    "children_info": false
  }
}
```

---

### 3. 収集情報・進捗の取得

**GET /api/sessions/{session_id}/status**
- 現在までに抽出されたプロフィール・進捗・履歴の一括取得

---

### 4. セッション完了

**POST /api/sessions/{session_id}/complete**
- 必須情報が全て揃った段階で呼ばれ、「family_session_agent」に連携
- レスポンス例:
```json
{
  "message": "収集が完了しました。ありがとうございました。",
  "user_profile": { ... },
  "information_complete": true
}
```

---

### 5. 生成データへのアクセス

- `backend/tmp/user_sessions/<session_id>/user_profile.json`：プロフィール
- `backend/tmp/user_sessions/<session_id>/conversation_history.json`：会話履歴
- `backend/tmp/user_sessions/<session_id>/family_plan.json`：生成ストーリーや手紙等

---

## 収集情報と構造化プロセス

### 必須フィールド

#### A-1. 必須項目（Required Fields）
ユーザーに自然言語で答えてもらう必須情報（これらがnullだと完了しない）：

- **年齢** - 数値（例: 「33歳です」）
- **交際状況** - 既婚/交際中/独身など（例: 「独身です」）
- **パートナーの性格** - 自由記述（例: 「明るくて優しい人」「几帳面で計画的」）
  - 既婚/交際中: 実際のパートナーの性格
  - 独身: 理想のパートナーの性格
- **パートナーの外見・顔の特徴** - 自由記述（例: 「目が大きくて優しい印象、髪は肩まであるセミロング」）
  - 既婚/交際中: 実際のパートナーの外見的特徴
  - 独身: 理想のパートナーの外見イメージ
  - **画像生成に必須のため、必ず収集する**
- **ユーザー自身の性格** - 自由記述（例: 「社交的で新しいことが好き」「几帳面で計画的」）
- **子供の希望** - 人数と性別（例: 「女の子1人と男の子1人」「3人欲しい」）
  - 注意: 子供の性格は聞かない（親の性格から自動計算される）

- 居住地 (`location`)
- 収入レンジ (`income_range`)
- パートナー顔特徴 (`partner_face_description`)

### 補助・拡張フィールド（今後）

#### A-3. オプション項目（Optional Fields）
実装では定義されているが、現在のヒアリングフローでは基本的に収集しない（ユーザーが自発的に話した場合のみ記録）：

- 性別
- ライフスタイル
- 家族構成
- ライフスタイル
- 趣味 など

### LLMによる変換・保存

- ユーザーメッセージ→`_extract_information()`（Gemini APIプロンプト）
  - 必須項目をJSONとして抽出
  - 性格表現→BigFive数値へマッピング
  - 子供情報のみ配列形式必須

---

## 進捗管理・内部オブジェクト

- `user_profile` (pydantic)
- `information_progress` (進捗ブール値マッピング)
- `conversation_history` (発話リスト)

---

## Family Agent連携（転送フロー）

- 収集完了時、`transfer_to_agent`等を経てFamily Agent（会話シナリオやストーリー生成）へシームレス転送
- 生成データ例：家族の日常ストーリー、未来の子供からの手紙など

---

## 備考・運用ポイント

- API設計は拡張志向：今後の画像アップロード・子供毎プロファイル追加も容易
- セッションごとのJSONファイル保存で一貫した状態管理
- フロントエンドはREST, WebSocket両対応設計も可能

---

以上。
もし何か追加したい仕様・APIや設計フローがあればご指摘ください。
この最新状態を docs/hera_agent_api_design.md へ適用/保存も可能です。
