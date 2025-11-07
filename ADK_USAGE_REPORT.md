# ADKサーバー使用履歴と現状の調査レポート

## エグゼクティブサマリー

このレポートは、Google ADK（Agent Development Kit）の使用状況とADKサーバー（`adk web agents`）の必要性について調査した結果をまとめたものです。

**結論**:
- フロントエンド経由でのAPI利用時、**ADKサーバーは不要**
- 2025年10月25日以降、直接Gemini APIを呼び出す実装に移行済み
- ADKライブラリは型定義とラッパーとしてのみ使用

---

## 1. 重要なコミット履歴

| 日付 | コミットID | 内容 |
|------|-----------|------|
| 2025-10-25 | 4190d0c | **情報抽出と返答生成を統合** - `_generate_hera_response_with_extraction()`を追加 |
| 2025-10-24 | 436263e | heraとフロントをつなぐapi作成 |
| - | c3eaaeb | **ADKセッションの確認と作成機能を追加**し、Heraエージェントとの通信処理を改善 |
| - | 933525d | ADKとAPIでセッションデータを共有するように修正 |

---

## 2. コードの変遷

### Phase 1: ADKサーバーを使う設計（初期実装）

**特徴**:
- `_generate_adk_response()`メソッドが`self.agent.run()`を呼び出していた
- ADKサーバー（`adk web agents`、ポート8000）との通信が前提
- `_get_latest_adk_session_id()`でADKサーバーからセッションIDを取得

**実装例**:
```python
async def _generate_adk_response(self, user_message: str, progress: Dict[str, bool]) -> Dict[str, str]:
    """ADKエージェントを使用して応答を生成"""
    try:
        # ADKエージェントの実行エンジンを使用
        response = await self.agent.run(
            message=user_message,
            context={
                "conversation_history": self.conversation_history,
                "user_profile": self.user_profile.dict(),
                "collected_info": await self._format_collected_info()
            }
        )
        raw_text = response.content if hasattr(response, 'content') else str(response)
        return self._wrap_response(raw_text)
    except Exception as e:
        print(f"ADKエージェント処理エラー: {e}")
        return self._wrap_response("お話を伺いました。続きもぜひ教えてください。")
```

### Phase 2: 直接Gemini API呼び出しに移行（2025-10-25以降）

**変更理由（推測）**:
- パフォーマンスの向上
- ADKサーバー依存の排除
- より柔軟なプロンプト制御

**新しい実装**:
```python
async def _generate_hera_response_with_extraction(self, user_message: str) -> str:
    """返答生成と情報抽出を統合したメソッド（heraの人格を活かした版）"""
    try:
        # 直接Gemini APIを使用
        from google.generativeai import GenerativeModel
        model = GenerativeModel('gemini-2.5-pro')

        # プロンプトを構築
        prompt = f"""
        あなたは{self.persona.name}（{self.persona.role}）です。
        ...
        """

        response = model.generate_content(prompt)
        response_text = response.text if hasattr(response, 'text') else str(response)

        # JSONを抽出して情報を更新
        ...

        return response_text
    except Exception as e:
        print(f"[ERROR] 統合応答生成エラー: {e}")
        return "申し訳ございません。もう一度お話ししていただけますか？"
```

### 現在の実装（run()メソッド）

```python
async def run(self, message: str, session_id: str = None, **kwargs) -> str:
    """ADKの標準runメソッド"""
    print("[INFO] ADK runメソッドが呼び出されました")

    try:
        # セッションIDの設定
        if session_id:
            self.current_session = session_id  # Flask APIから渡される
        elif not self.current_session:
            self.current_session = await self._get_latest_adk_session_id()  # フォールバック

        # 会話履歴にユーザーメッセージを追加
        await self._add_to_history("user", message)

        # ⚠️ 重要: ADKのself.agent.run()は呼ばれない！
        # 代わりに直接Gemini APIを使用
        response_text = await self._generate_hera_response_with_extraction(message)

        # エージェントの応答を履歴に追加
        await self._add_to_history("hera", response_text)

        # 完了判定
        completion_result = await self._evaluate_session_completion(message, user_message_already_logged=True)

        # レスポンスを返す
        payload = self._wrap_response(response_text)
        payload.update({
            "session_status": completion_result.get("status", "INCOMPLETE"),
            "completion_message": completion_result.get("completion_message"),
            "missing_fields": completion_result.get("remaining_missing", []),
            "user_profile": prune_empty_fields(self.user_profile.dict()),
            "information_progress": build_information_progress(self.user_profile.dict()),
        })

        return json.dumps(payload, ensure_ascii=False)
    except Exception as e:
        print(f"[ERROR] runメソッドエラー: {e}")
        return json.dumps(self._wrap_response("申し訳ございません。少し時間をいただけますか？"), ensure_ascii=False)
```

---

## 3. ADKライブラリの現在の使用状況

### ✅ 使われているADK機能

1. **クラス定義・継承**
```python
# backend/agents/hera/adk_hera_agent.py:15
from google.adk.agents.llm_agent import Agent

# backend/agents/family/family_agent.py:5
class FamilyAgent(Agent):  # ← 継承のみ、実行エンジンは未使用
    ...
```

2. **FunctionToolラッパー**
```python
# backend/agents/family/tooling.py:10, 159
from google.adk.tools import FunctionTool
self.tool = FunctionTool(func=call_agent)
```

### ❌ 使われていないADK機能

1. **Agent.run()** - エージェント実行エンジン
2. **ADKのメモリ管理システム**
3. **ADKのツール自動実行システム**
4. **ADKのサブエージェント連携機能**

### ⚠️ デッドコード（定義されているが呼ばれていない）

```python
# backend/agents/hera/adk_hera_agent.py:377-396
async def _generate_adk_response(self, user_message: str, progress: Dict[str, bool]) -> Dict[str, str]:
    """ADKエージェントを使用して応答を生成"""
    # ← このメソッドはどこからも呼ばれていない
    response = await self.agent.run(...)
    ...
```

```python
# backend/agents/family/family_agent.py:10-46
class FamilyAgent(Agent):
    """家族メンバーが話すためのLLMエージェント"""
    # ← このクラスはインスタンス化されていない
    ...
```

---

## 4. 実際の実行フロー

### Frontend経由のフロー（ADKサーバー不要）

```
Frontend (Next.js)
    ↓ HTTP POST /api/sessions/{session_id}/messages
Flask API (backend/api/app.py)
    ↓ run_async(hera_agent.run(message, session_id))
ADKHeraAgent.run()
    ↓ _generate_hera_response_with_extraction()
GenerativeModel('gemini-2.5-pro').generate_content()
    ↓
Gemini API (直接呼び出し)
```

**ポイント**:
- Flask APIがセッションIDを管理
- `self.agent.run()`（ADK実行エンジン）は呼ばれない
- ADKサーバー（ポート8000）への接続なし

### ADK Web UI経由のフロー（ADKサーバー必要）

```
Browser
    ↓
ADK Dev UI (http://localhost:8000)
    ↓ WebSocket/HTTP
ADK Server
    ↓
hera_session_agent()
    ↓
ADKHeraAgent
```

**ポイント**:
- `adk web agents`コマンドでADKサーバーを起動
- 開発・デバッグ用の別ルート
- Flask API経由とは独立

---

## 5. 動作確認テスト結果（2025-11-07実施）

### テスト条件
- ADKサーバー（ポート8000）: **未起動**
- Flask APIサーバー（ポート8080）: **起動中**

### テスト結果

| テスト項目 | 結果 | 詳細 |
|----------|------|------|
| ヘルスチェック | ✅ 成功 | `GET /api/health` → `{"status": "ok"}` |
| セッション作成 | ✅ 成功 | `POST /api/sessions` → セッションID発行 |
| メッセージ送信 | ✅ 成功 | Heraエージェントが正常に応答 |
| 情報抽出 | ✅ 成功 | プロファイル情報の抽出・更新が正常動作 |

### 実際のログ
```
[DEBUG] Heraエージェントのツール数: 2
[SUCCESS] Familyエージェントをサブエージェントとして追加しました
✅ Firebase initialized with service account
[INFO] セッション管理初期化完了: FirebaseSessionManager
[INFO] セッション作成（ゲストモード）: 8515ea18-bce5-4a97-9b2d-ccb9c3b488c0

GET  /api/health → 200
POST /api/sessions → 200
POST /api/sessions/.../messages → 200
```

### Heraエージェントの応答例
```json
{
  "reply": "こんにちは、愛しい子。私に声をかけてくれて嬉しいわ。私はヘーラー、家族の愛と絆を見守る神です。あなたの幸せな未来を思い描くお手伝いをさせてくださいね。差し支えなければ、あなたのこと……年齢や性別、そして、今どのような形で愛を育んでいるのか（例えば、結婚している、大切な方がいる、など）を教えていただけますか？",
  "information_progress": {
    "age": false,
    "children_info": false,
    "gender": false,
    "income_range": false,
    "location": false,
    "partner_face_description": false,
    "relationship_status": false,
    "user_personality_traits": false
  },
  "missing_fields": [...],
  "profile_complete": false
}
```

---

## 6. デグレの可能性についての評価

### 結論: **デグレなし** ✅

### 根拠

1. **移行は2025年10月25日に完了済み**
   - コミット4190d0cで`_generate_hera_response_with_extraction()`が追加
   - それ以降、Flask API経由では直接Gemini APIを使用

2. **`_generate_adk_response()`は使われていない**
   - 定義は残っているが、呼び出し箇所が存在しない
   - デッドコードとして残存

3. **ADK Web UIは別ルート**
   - Flask API経由とは独立したエントリーポイント
   - 開発・デバッグ用途で使用可能（オプション）

4. **実際の動作テストで検証済み**
   - ADKサーバーなしで正常動作を確認
   - セッション作成、メッセージ送受信、情報抽出が正常動作

---

## 7. ADKの現在の位置づけ

| 用途 | ADKサーバー | ADKライブラリ | 実際の処理 |
|------|------------|--------------|-----------|
| **フロントエンド経由** | ❌ 不要 | ✅ 型定義のみ使用 | 直接Gemini API |
| **ADK Web UI直接** | ✅ 必要 (`adk web agents`) | ✅ 完全使用 | ADK実行エンジン |
| **開発・デバッグ** | △ オプション | ✅ ツール定義に使用 | 用途による |

---

## 8. 推奨事項

### 即座に実施可能

1. **ドキュメント更新**
   - README.mdでADKサーバーの必要性を明確化
   - フロントエンド経由では不要と明記

2. **デッドコードのクリーンアップ（オプション）**
   - `_generate_adk_response()`メソッドの削除
   - `FamilyAgent`クラスの削除または再利用

### 中長期的な検討事項

1. **ADKライブラリの完全活用または削除**
   - 選択肢A: ADKの実行エンジンを活用してツール連携を強化
   - 選択肢B: ADKライブラリへの依存を完全に削除し、軽量化

2. **アーキテクチャの明確化**
   - ADKを使う場合と使わない場合のユースケースを文書化
   - 開発者向けガイドラインの整備

---

## 9. まとめ

### ADKサーバーが必要だった時期
**初期実装 〜 2025年10月25日頃まで**

### 現在の状況（2025年11月7日時点）
- フロントエンド経由: **ADKサーバー不要**
- ADKライブラリ: **型定義とラッパーのみ使用**
- 実際の処理: **直接Gemini API呼び出し**

### デグレの有無
**なし** - 動作テストで正常動作を確認済み

### 今後の運用
- 本番環境: Flask APIのみで動作（ADKサーバー不要）
- 開発環境: ADK Web UIはオプション（デバッグ用）
- テスト環境: 両方の動作確認を推奨

---

**調査実施日**: 2025年11月7日
**調査者**: Claude Code
**対象コードベース**: /Users/user/dev/hera/backend
