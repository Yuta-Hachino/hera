# Heraエージェント API設計ドキュメント

## 概要
ヘラエージェント（家族愛AI）とフロントエンド間のやりとりを行うためのAPI設計です。セッション管理・情報抽出・履歴/状態同期を軸に、運用や拡張性も考慮した設計となっています。

---

## エージェント基幹処理とAPI設計

- セッション単位でプロフィール・履歴・状態を管理
- ユーザーメッセージ送信でLLMによる自動抽出＆進捗管理
- 履歴やプロフィール、進捗の取得・明示終了などにも対応

---

## APIエンドポイント一覧

### 1. セッション開始
|メソッド|パス|
|:--|:--|
|POST|/api/sessions|

#### リクエスト
```json
{
  "user_id": "string（任意）"
}
```

#### レスポンス
```json
{
  "session_id": "abc-123-xyz",
  "created_at": "2025-10-22T12:01:23",
  "status": "created"
}
```

---

### 2. メッセージ送信・情報抽出
|メソッド|パス|
|:--|:--|
|POST|/api/sessions/{session_id}/messages|

#### リクエスト
```json
{
  "message": "29歳のエンジニアで東京在住です。家族は妻と子供2人です。"
}
```

#### レスポンス
```json
{
  "reply": "素敵なご家族ですね。奥様やお子様について、もっと教えていただけますか？",
  "conversation_history": [
    {"speaker": "user", "message": "29歳のエンジニア ..."},
    {"speaker": "hera", "message": "素敵なご家族ですね ..."}
  ],
  "user_profile": {
    "age": 29, "work_style": "エンジニア", "location": "東京", 
    "family_structure": {"wife": 1, "children": 2}
  },
  "information_progress": {
    "age": true, "gender": false, "income_range": false
  }
}
```
---

### 3. セッション進捗・状態取得
|メソッド|パス|
|:--|:--|
|GET|/api/sessions/{session_id}/status|

#### レスポンス
```json
{
  "user_profile": { ... },
  "information_progress": { ... },
  "conversation_history": [ ... ]
}
```

---

### 4. セッション終了（完了保存）
|メソッド|パス|
|:--|:--|
|POST|/api/sessions/{session_id}/complete|

#### リクエスト
```json
{}
```

#### レスポンス
```json
{
  "message": "収集が完了しました。ありがとうございました。",
  "user_profile": { ... },
  "information_complete": true
}
```

---

## 実装意図・運用ポイント

- **メッセージ送信APIで「LLM抽出結果」「最新プロファイル」「進捗」すべて返す設計**
- **写真アップロード・拡張性：今後必要に応じ追加可**
- **FastAPI/Flask等の非同期実装しやすい構成**
- **セッションごとにADKHeraAgentを内部で管理・切り替え（tmp保存＋メモリ保持想定）**
- **`user_profile`, `information_progress`フィールドで進捗UIも構築しやすい**

---

## 参考：収集情報フィールド（例）

### 必須項目（Required Fields）
これらの情報が揃わないとFamily Agentへの転送ができません：

- **`age`** - 年齢（数値）
- **`relationship_status`** - 交際状況
  - 値: `"married"` (既婚), `"partnered"` (交際中), `"single"` (独身), `"other"` (その他)
- **`current_partner`** または **`ideal_partner`** - パートナー情報
  - `current_partner`: 現在のパートナー情報（既婚/交際中の場合）
  - `ideal_partner`: 理想のパートナー像（独身の場合）
  - 共通フィールド:
    - `personality_traits`: ビッグファイブ性格特性（詳細は下記）
    - `temperament`: 性格の総合的な説明（文字列）
    - `hobbies`: 趣味（文字列配列）
    - `speaking_style`: 話し方の特徴（文字列）
- **`user_personality_traits`** - ユーザー自身の性格特性（ビッグファイブモデル）
  - `openness`: 開放性 (0.0-1.0) - 好奇心旺盛さ、新しいこと好き
  - `conscientiousness`: 誠実性 (0.0-1.0) - 几帳面さ、計画的
  - `extraversion`: 外向性 (0.0-1.0) - 社交性、明るさ、活発さ
  - `agreeableness`: 協調性 (0.0-1.0) - 優しさ、思いやり
  - `neuroticism`: 神経症傾向 (0.0-1.0) - 心配性さ、慎重さ
- **`children_info`** - 子どもの希望情報（配列形式）
  - 各要素: `{ "desired_gender": "男" | "女" }`
  - 例: `[{"desired_gender": "女"}, {"desired_gender": "男"}]` - 女の子1人、男の子1人

### 推奨項目（Recommended Fields）
収集推奨だが、なくてもFamily Agentへの転送は可能：

- **`location`** - 居住地（文字列）
- **`income_range`** - 収入範囲（文字列）

### オプション項目（Optional Fields）
実装では定義されているが、現在のヒアリングフローでは基本的に収集しない：

- `gender` - 性別
- `lifestyle` - ライフスタイル情報（辞書）
- `family_structure` - 家族構成（辞書）
- `interests` - 趣味・興味（文字列配列）
- `work_style` - 現在の仕事スタイル
- `future_career` - 将来の仕事・キャリア
- `partner_face_description` - 配偶者の顔の特徴の文章記述
- `created_at` - 作成日時（自動設定）

---

## 備考/今後の拡張
- 写真アップロードAPIを別途追加可能
- 会話履歴取得・ダウンロード、セッション一括管理、削除など
- OpenAPI（Swagger/Redoc）化も容易

---

以上
