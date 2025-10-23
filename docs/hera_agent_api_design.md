# Heraエージェント API設計ドキュメント（リニューアル版）

## 概要

Heraエージェントは、家族観や価値観ヒアリングを行いながら「未来の家族像」生成・会話体験を実現するAIサービスです。  主に**セッション単位**でプロフィール・会話履歴・進捗状態を管理し、LLMを通じてユーザー情報を抽出・構造化、家族ペルソナ生成やFamily Agentへの転送までを担います。

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
