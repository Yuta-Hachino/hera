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

### 【A】ユーザーから自然言語で収集する情報（生データ）

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

#### A-2. 推奨項目（Recommended Fields）
収集推奨だが、なくてもFamily Agentへの転送は可能：

- **居住地** - 自由記述（例: 「東京都港区」）
- **収入範囲** - 自由記述（例: 「年収500-700万円」）

#### A-3. オプション項目（Optional Fields）
実装では定義されているが、現在のヒアリングフローでは基本的に収集しない（ユーザーが自発的に話した場合のみ記録）：

- 性別
- ライフスタイル
- 家族構成
- 趣味・興味
- 現在の仕事スタイル
- 将来の仕事・キャリア

---

### 【B】LLMが自動的に抽出・推定する項目

ユーザーの自然言語回答（【A】）から、LLMが構造化データに変換：

#### B-1. 基本情報（直接抽出）
- **`age`** - 年齢（数値）
- **`relationship_status`** - 交際状況
  - 値: `"married"` (既婚), `"partnered"` (交際中), `"single"` (独身), `"other"` (その他)
- **`location`** - 居住地（文字列）
- **`income_range`** - 収入範囲（文字列）
- **`partner_face_description`** - パートナーの顔の特徴（文字列）

#### B-2. 性格特性の数値化（推定・変換）
ユーザーの自然言語での性格描写を **ビッグファイブモデルの数値** に変換：

- **`user_personality_traits`** - ユーザー自身の性格特性（ビッグファイブ）
  - `openness`: 開放性 (0.0-1.0) - 好奇心旺盛さ、新しいこと好き
  - `conscientiousness`: 誠実性 (0.0-1.0) - 几帳面さ、計画的
  - `extraversion`: 外向性 (0.0-1.0) - 社交性、明るさ、活発さ
  - `agreeableness`: 協調性 (0.0-1.0) - 優しさ、思いやり
  - `neuroticism`: 神経症傾向 (0.0-1.0) - 心配性さ、慎重さ

- **パートナーの性格特性**（`current_partner.personality_traits` または `ideal_partner.personality_traits`）
  - 同様にビッグファイブの数値に変換
  - `temperament`: 性格の総合的な説明（文字列として保持）
  - `hobbies`: 趣味（言及があれば抽出）
  - `speaking_style`: 話し方の特徴（推定）

#### B-3. 子供情報の構造化
- **`children_info`** - 子どもの希望情報（配列形式）
  - 各要素: `{ "desired_gender": "男" | "女" }`
  - 例: 「女の子1人と男の子1人」 → `[{"desired_gender": "女"}, {"desired_gender": "男"}]`

**抽出方法**: `_extract_information()` メソッドがGemini APIを使用してプロンプトベースで抽出
**実装**: `backend/agents/hera/adk_hera_agent.py:307-427`

---

### 【C】内部的に自動生成される項目（計算・合成）

【B】で抽出された構造化データを基に、さらに高度な処理を実行：

#### C-1. 子どもの性格特性（自動計算）
- **計算方法**: `PersonalityCalculator`が親のビッグファイブ性格特性から科学的に計算
- **入力**: `user_personality_traits` + `current_partner.personality_traits` (または `ideal_partner.personality_traits`)
- **出力**: 各子どもの`BigFiveTraits`（遺伝と環境を考慮した確率的モデル）
- **実装**: `backend/agents/family/personality_calculator.py`
- **詳細**:
  - 遺伝的影響: 40-50%（両親の平均値付近に分布）
  - 環境的影響: ランダム要因を追加
  - 出生順位による補正（第1子は責任感高め、末子は社交性高めなど）

#### C-2. 子どもの具体的な性格描写（LLM生成）
- **生成内容**:
  - `speaking_style`: 話し方の特徴
  - `traits`: 性格特性リスト（日本語）
  - `goals`: 目標や願い
  - `personality_description`: 性格の総合的な説明
- **生成方法**: `PersonalityCalculator.generate_personality_description()`がGemini APIを使用してビッグファイブから具体的な描写を生成
- **実装**: `backend/agents/family/personality_calculator.py:57-104`

#### C-3. パートナーの性格特性リスト（変換）
- **変換内容**: ビッグファイブの数値を日本語の特徴リストに変換
- **例**: `openness > 0.6` → 「好奇心旺盛」
- **実装**: `persona_factory.py:242-257` の `_traits_from_big_five()`

#### C-4. システム管理項目
- **`created_at`** - プロファイル作成日時（自動設定）
- **会話履歴** - Hera Agentとのやり取り（自動記録）
- **セッション情報** - セッションID、最終更新時刻など

---

### 【D】データフロー概要

```
[ユーザー入力（自然言語）]
  ↓ Hera Agentがヒアリング
[A: 自然言語で情報を収集]
  - 年齢、交際状況
  - パートナーの性格（自由記述）
  - パートナーの外見（自由記述）
  - ユーザー自身の性格（自由記述）
  - 子供の希望（自由記述）
  ↓
[B: LLMが構造化データに抽出・変換]
  ↓ _extract_information() → Gemini API
  - B-1: 基本情報を抽出
    - age, relationship_status, location, partner_face_description
  - B-2: 性格を数値化
    - 「明るくて優しい」→ user_personality_traits: {extraversion: 0.7, agreeableness: 0.8, ...}
    - 「几帳面で計画的」→ partner.personality_traits: {conscientiousness: 0.8, ...}
  - B-3: 子供情報を構造化
    - 「女の子1人と男の子1人」→ [{desired_gender: "女"}, {desired_gender: "男"}]
  ↓ 保存 (user_profile.json)
[Family Agentに転送]
  ↓ PersonaFactory実行
[C: さらなる自動生成・計算]
  - C-1: 子どもの性格を計算
    - PersonalityCalculator.calculate_child_traits()
    - 親のビッグファイブ → 子どものビッグファイブ（遺伝モデル）
  - C-2: 具体的な性格描写を生成
    - LLMで speaking_style, traits, goals等を生成
  - C-3: 日本語特性リストに変換
  ↓
[家族ペルソナ完成]
  - Partner Persona (B-1, B-2から構築)
  - Children Personas (C-1, C-2から構築)
```

---

## 備考/今後の拡張
- 写真アップロードAPIを別途追加可能
- 会話履歴取得・ダウンロード、セッション一括管理、削除など
- OpenAPI（Swagger/Redoc）化も容易

---

以上
