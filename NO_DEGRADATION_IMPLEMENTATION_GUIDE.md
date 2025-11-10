# 機能デグレ防止 - 実装ガイドライン

**作成日**: 2025-11-10
**目的**: Gemini Live API統合時に既存機能を一切壊さないための厳格なガイドライン

---

## 🚨 重要原則

### 絶対に守るべき3つの原則

1. **既存エンドポイントは一切変更しない**
2. **既存の動作は完全に維持する**
3. **新機能は既存機能から完全に分離する**

---

## 📋 既存機能の保護リスト

### 保護対象：既存APIエンドポイント（絶対に変更禁止）

| エンドポイント | 用途 | 保護理由 |
|--------------|------|----------|
| `POST /api/sessions` | セッション作成 | 🔴 最重要：全ての起点 |
| `POST /api/sessions/<id>/messages` | テキストメッセージ送信 | 🔴 最重要：既存の対話機能 |
| `GET /api/sessions/<id>/status` | ステータス取得 | 🔴 重要：UI表示に使用 |
| `POST /api/sessions/<id>/complete` | セッション完了 | 🔴 重要：情報収集完了 |
| `GET /api/sessions/<id>/family/status` | 家族エージェントステータス | 🟡 重要 |
| `POST /api/sessions/<id>/family/messages` | 家族エージェントメッセージ | 🟡 重要 |
| `GET /api/health` | ヘルスチェック | 🟢 監視用 |
| `POST /api/sessions/<id>/photos/user` | 画像アップロード | 🟡 重要 |
| `GET /api/sessions/<id>/photos/<filename>` | 画像取得 | 🟡 重要 |
| `POST /api/sessions/<id>/generate-image` | パートナー画像生成 | 🟡 重要 |
| `POST /api/sessions/<id>/generate-child-image` | 子供画像生成 | 🟡 重要 |

### 保護対象：既存のコア機能

| 機能 | ファイル | 保護内容 |
|------|---------|----------|
| **ADKHeraAgent** | `agents/hera/adk_hera_agent.py` | `run()`, `start_session()`, `_generate_hera_response_with_extraction()` など既存メソッドは変更禁止 |
| **FamilyAgent** | `agents/family/family_agent.py` | 家族会話機能は変更禁止 |
| **SessionManager** | `utils/session_manager.py` | File/Redis/Supabase対応は変更禁止 |
| **StorageManager** | `utils/storage_manager.py` | 画像保存機能は変更禁止 |

---

## ✅ 新機能追加の正しい方法

### 方針1: 新規エンドポイントとして追加

#### ✅ 正しい実装（既存に影響なし）

```python
# backend/api/app.py に追加

# 🆕 新規エンドポイント（既存に影響なし）
@app.route('/api/sessions/<session_id>/ephemeral-token', methods=['POST'])
@optional_auth
def create_ephemeral_token(session_id):
    """Gemini Live API用のEphemeralトークンを生成（新機能）"""
    # GEMINI_LIVE_MODEがdisabledの場合は503エラー
    if not os.getenv('GEMINI_LIVE_MODE', 'disabled') == 'enabled':
        return jsonify({'error': 'Live API機能が無効です'}), 503

    # 既存のセッション機能を使用（read-only）
    if not session_exists(session_id):
        return jsonify({'error': 'セッションが存在しません'}), 404

    # 新しい機能を追加
    # ...
```

#### ❌ 間違った実装（既存を壊す）

```python
# backend/api/app.py を変更

# ❌ 既存エンドポイントを変更してはいけない
@app.route('/api/sessions/<session_id>/messages', methods=['POST'])
@optional_auth
def send_message(session_id):
    req = request.get_json()

    # ❌ 既存の動作を変更してはいけない
    if req.get('use_live_api'):  # ← これは追加してはいけない
        # Live API処理...
        pass

    # 既存の処理...
```

### 方針2: 既存クラスに新メソッドを追加（既存メソッドは変更しない）

#### ✅ 正しい実装

```python
# agents/hera/adk_hera_agent.py

class ADKHeraAgent:
    # 既存のメソッドは一切変更しない
    async def run(self, message: str, session_id: str = None, **kwargs) -> str:
        """既存の実装をそのまま維持"""
        # ...既存のコード...
        pass

    # 🆕 新しいメソッドを追加
    async def start_live_session(self, session_id: str, ephemeral_token: str) -> None:
        """Live API専用の新機能（既存に影響なし）"""
        if not os.getenv('GEMINI_LIVE_MODE', 'disabled') == 'enabled':
            raise ValueError("Live API機能が無効です")

        # 新しい機能を実装
        # ...
```

#### ❌ 間違った実装

```python
# agents/hera/adk_hera_agent.py

class ADKHeraAgent:
    # ❌ 既存のメソッドを変更してはいけない
    async def run(self, message: str, session_id: str = None, use_live_api: bool = False, **kwargs) -> str:
        """既存メソッドに新パラメータを追加してはいけない"""

        # ❌ 既存の動作フローを変更してはいけない
        if use_live_api:
            return await self._run_with_live_api(message, session_id)

        # 既存のコード...
```

### 方針3: 環境変数で機能のON/OFF制御

#### ✅ 正しい実装

```python
# backend/api/app.py

# Live API機能は環境変数で制御（デフォルトOFF）
LIVE_API_ENABLED = os.getenv('GEMINI_LIVE_MODE', 'disabled').lower() == 'enabled'

if LIVE_API_ENABLED:
    try:
        from utils.ephemeral_token_manager import get_ephemeral_token_manager
        ephemeral_token_mgr = get_ephemeral_token_manager()
        logger.info("✅ Gemini Live API機能: 有効")
    except Exception as e:
        logger.warning(f"⚠️ Live API初期化失敗: {e}")
        LIVE_API_ENABLED = False
else:
    logger.info("ℹ️ Gemini Live API機能: 無効（既存機能のみ）")

# 既存のHeraエージェントは常に初期化（Live APIとは無関係）
hera_agent = ADKHeraAgent(gemini_api_key=os.getenv("GEMINI_API_KEY"))
```

---

## 🧪 デグレ防止テスト

### Phase 1実装前の必須テスト

```bash
# 1. 既存機能が動作することを確認
cd backend
python -m pytest tests/ -v

# 2. 既存APIエンドポイントのテスト
curl -X POST http://localhost:8080/api/sessions
curl -X POST http://localhost:8080/api/sessions/{session_id}/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "こんにちは"}'
curl -X GET http://localhost:8080/api/sessions/{session_id}/status

# 3. ヘルスチェック
curl -X GET http://localhost:8080/api/health
```

### Phase 1実装後の必須テスト

```bash
# 1. 既存機能が引き続き動作することを確認（デグレチェック）
cd backend
python -m pytest tests/ -v

# 2. 既存APIエンドポイントが変わらず動作することを確認
curl -X POST http://localhost:8080/api/sessions
curl -X POST http://localhost:8080/api/sessions/{session_id}/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "こんにちは"}'

# 3. Live API機能が無効の場合の動作確認
GEMINI_LIVE_MODE=disabled python api/app.py
# → 既存機能は正常動作、Live APIエンドポイントは503エラー

# 4. Live API機能が有効の場合の動作確認
GEMINI_LIVE_MODE=enabled python api/app.py
# → 既存機能も正常動作、Live APIエンドポイントも動作
```

---

## 📝 実装チェックリスト

### Phase 1: 基礎実装（Week 1-2）

- [ ] **既存コードのバックアップ**: `git commit -m "Phase 1実装前のバックアップ"`
- [ ] **既存機能のテスト実行**: すべてのテストが通ることを確認
- [ ] **新規ファイルの追加**: `utils/ephemeral_token_manager.py`（既存ファイルは変更しない）
- [ ] **環境変数の追加**: `.env.example`に追加（既存の環境変数は変更しない）
- [ ] **新規エンドポイントの追加**: `app.py`の末尾に追加（既存エンドポイントは変更しない）
- [ ] **デグレテストの実行**: 既存APIエンドポイントがすべて動作することを確認

### Phase 2: 音声I/O（Week 3-4）

- [ ] **既存コードのバックアップ**: `git commit -m "Phase 2実装前のバックアップ"`
- [ ] **新規ファイルの追加**: `utils/audio_utils.py`（既存ファイルは変更しない）
- [ ] **フロントエンド新規ファイル**: `lib/audio/*`（既存ファイルは変更しない）
- [ ] **デグレテストの実行**: 既存機能がすべて動作することを確認

### Phase 3: UI/UX（Week 5-6）

- [ ] **既存コードのバックアップ**: `git commit -m "Phase 3実装前のバックアップ"`
- [ ] **新規コンポーネントの追加**: `components/live/*`（既存コンポーネントは変更しない）
- [ ] **デグレテストの実行**: 既存UIがすべて動作することを確認

### Phase 4: ADKエージェント統合（Week 7-8）

- [ ] **既存コードのバックアップ**: `git commit -m "Phase 4実装前のバックアップ"`
- [ ] **ADKHeraAgentに新メソッド追加**: 既存の`run()`メソッドは一切変更しない
- [ ] **新メソッドのみテスト**: `start_live_session()`, `send_audio_chunk()`など
- [ ] **デグレテストの実行**: 既存のテキスト対話機能がすべて動作することを確認

### Phase 5: テスト・最適化（Week 9-10）

- [ ] **統合テスト**: 既存機能 + 新機能の両方がエラーなく動作
- [ ] **パフォーマンステスト**: 既存機能のレスポンス時間が劣化していないことを確認
- [ ] **本番デプロイ前の最終確認**: すべての既存機能が動作することを確認

---

## 🚨 デグレが発生した場合の対処

### 即座にロールバック

```bash
# 1. 変更を破棄
git reset --hard HEAD~1

# 2. 既存機能のテスト
python -m pytest tests/ -v

# 3. 問題の原因を特定
git diff HEAD HEAD~1

# 4. 修正後に再度実装
```

### デグレの報告

```
デグレ報告:
- 発生フェーズ: Phase X
- 影響範囲: [影響を受けたエンドポイント/機能]
- 原因: [具体的な変更内容]
- 対処: [ロールバックまたは修正内容]
```

---

## 📊 デグレ防止のメトリクス

### 各フェーズ実装後に確認する指標

| 指標 | 期待値 | 測定方法 |
|------|--------|----------|
| **既存APIのレスポンスタイム** | 変化なし（±5%以内） | `time curl ...` |
| **既存テストの成功率** | 100% | `pytest tests/` |
| **既存エンドポイントのHTTPステータス** | 200/201（変化なし） | `curl -I ...` |
| **既存機能のエラー率** | 0% | ログファイル確認 |
| **既存UIの表示速度** | 変化なし | Lighthouseスコア |

---

## 💡 ベストプラクティス

### 1. Git Commitの粒度

```bash
# ✅ 良い例：小さく、ロールバック可能
git commit -m "Add ephemeral_token_manager.py (新規ファイル)"
git commit -m "Add /api/sessions/<id>/ephemeral-token endpoint (既存に影響なし)"
git commit -m "Add GEMINI_LIVE_MODE env var (既存機能は無効時も動作)"

# ❌ 悪い例：大きすぎる、ロールバック困難
git commit -m "Add Gemini Live API integration with backend changes"
```

### 2. ブランチ戦略

```bash
# 機能ごとにブランチを分ける
git checkout -b feature/live-api-phase1-foundation
git checkout -b feature/live-api-phase2-audio-io
git checkout -b feature/live-api-phase3-ui

# 各ブランチで既存機能のテストを実行してからマージ
```

### 3. コードレビューのポイント

- [ ] 既存ファイルの変更が最小限か？
- [ ] 既存メソッドのシグネチャが変わっていないか？
- [ ] 既存のエンドポイントが変更されていないか？
- [ ] 新機能が環境変数で無効化できるか？
- [ ] 既存のテストがすべて通るか？

---

## 🎯 まとめ

### デグレ防止の3原則（再掲）

1. **既存エンドポイントは一切変更しない** → 新規エンドポイントとして追加
2. **既存の動作は完全に維持する** → 新メソッドを追加、既存メソッドは変更しない
3. **新機能は既存機能から完全に分離する** → 環境変数で制御、デフォルトOFF

### 実装時の心構え

- ✅ **慎重に**: 1行の変更でも既存機能に影響がないか確認
- ✅ **段階的に**: 小さなコミットで進める
- ✅ **テスト駆動**: 実装前後で必ずテスト実行
- ✅ **ロールバック可能**: いつでも元に戻せる状態を維持

---

**このガイドラインに従えば、既存機能を一切壊すことなくGemini Live APIを統合できます！**
