# Gemini Live API統合 - クイックスタートガイド

**今すぐ始めるための実装手順書**

---

## 🚀 今日から始める3ステップ

### Step 1: 環境準備（15分）

```bash
# 1. 依存関係のインストール
cd backend
pip install websockets==12.0 google-genai>=0.8.0 pyaudio==0.2.14 pydub==0.25.1 numpy==1.26.0

cd ../frontend
npm install wavesurfer.js@^7.0.0

# 2. 環境変数を設定
cd ../backend
cp .env.example .env
# .envを編集して以下を追加：
# GEMINI_LIVE_MODE=enabled
# GEMINI_LIVE_MODEL=gemini-2.0-flash-live-preview-04-09
# AUDIO_INPUT_ENABLED=false  # 音声入力デフォルトOFF
```

### Step 2: 基本実装（1時間）

#### EphemeralTokenManagerを作成

```bash
# backend/utils/ephemeral_token_manager.py を作成
# 内容は GEMINI_LIVE_API_INTEGRATION_PLAN.md の Task 1.3 を参照
```

#### APIエンドポイントを追加

```python
# backend/api/app.py に以下を追加：

from utils.ephemeral_token_manager import get_ephemeral_token_manager

# Ephemeralトークン生成API
@app.route('/api/sessions/<session_id>/ephemeral-token', methods=['POST'])
@optional_auth
def create_ephemeral_token(session_id):
    """Ephemeralトークンを生成して返す"""
    if not session_exists(session_id):
        return jsonify({'error': 'セッションが存在しません'}), 404

    try:
        ephemeral_token_mgr = get_ephemeral_token_manager()
        token_data = ephemeral_token_mgr.create_token()

        return jsonify({
            'token': token_data['token'],
            'expire_time': token_data['expire_time'],
            'model': token_data['model'],
            'ws_endpoint': 'wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent'
        })
    except Exception as e:
        return jsonify({'error': 'トークン生成に失敗しました'}), 500
```

### Step 3: 動作確認（15分）

```bash
# 接続テストスクリプトを実行
cd backend
python tests/test_live_api_connection.py

# 成功すれば、WebSocket接続が確立されます！
```

---

## 📅 Week-by-Week実装ガイド

### Week 1-2: 基礎実装
- [x] **Day 1**: 依存関係インストール、環境変数設定
- [x] **Day 2-3**: EphemeralTokenManager実装、APIエンドポイント追加
- [x] **Day 4-5**: WebSocket接続テスト

**成果物**: Ephemeralトークン生成APIとWebSocket接続テスト

### Week 3-4: 音声I/O
- [ ] **Day 1-2**: 音声ユーティリティ実装（audio_utils.py）
- [ ] **Day 3-5**: AudioRecorder実装（マイク入力16kHz PCM）
- [ ] **Day 6-8**: AudioPlayer実装（音声出力24kHz PCM）

**成果物**: 音声の録音・再生機能

### Week 5-6: UI/UX
- [ ] **Day 1-3**: LiveSessionManager実装（WebSocket統合）
- [ ] **Day 4-5**: LiveChatInterface実装（音声チャットUI）
- [ ] **Day 6-7**: AudioVisualizer実装（波形表示）

**成果物**: 音声チャットインターフェース

### Week 7-8: ADKエージェント統合
- [ ] **Day 1-5**: ADKHeraAgent拡張（Live API対応）
- [ ] **Day 6-8**: セッション管理統合、エラーハンドリング

**成果物**: ADKエージェントの音声対応

### Week 9-10: テスト・最適化
- [ ] **Day 1-5**: 統合テスト、バグ修正
- [ ] **Day 6-10**: パフォーマンス最適化
- [ ] **Day 11-13**: 本番デプロイ

**成果物**: 本番環境での音声チャット機能

---

## 🎯 マイルストーン

### Milestone 1: 基礎完成（Week 2終了時）
- ✅ Ephemeralトークン生成機能
- ✅ WebSocket接続確立
- ✅ テキストメッセージ送受信

**デモ**: WebSocketでテキストメッセージをやり取り

### Milestone 2: 音声I/O完成（Week 4終了時）
- ✅ マイク入力（16kHz PCM）
- ✅ 音声出力（24kHz PCM）
- ✅ Web Audio API統合

**デモ**: マイクから音声を録音し、再生

### Milestone 3: UI完成（Week 6終了時）
- ✅ 音声チャットUI
- ✅ 音声可視化（波形表示）
- ✅ VAD UI

**デモ**: ブラウザで音声チャットが動作

### Milestone 4: ADK統合完成（Week 8終了時）
- ✅ ADKHeraAgentの音声対応
- ✅ セッション管理統合
- ✅ エラーハンドリング

**デモ**: ヘーラーエージェントと音声で対話

### Milestone 5: 本番リリース（Week 10終了時）
- ✅ 全機能統合
- ✅ パフォーマンス最適化
- ✅ 本番デプロイ

**デモ**: 本番環境で音声チャット機能を公開

---

## 📂 ファイル構成

### 新規作成ファイル

```
hera/
├── backend/
│   ├── utils/
│   │   ├── ephemeral_token_manager.py    # NEW
│   │   └── audio_utils.py                # NEW
│   └── tests/
│       ├── test_live_api_connection.py   # NEW
│       └── test_live_integration.py      # NEW
│
└── frontend/
    ├── lib/
    │   ├── audio/
    │   │   ├── AudioRecorder.ts          # NEW
    │   │   └── AudioPlayer.ts            # NEW
    │   └── live/
    │       └── LiveSessionManager.ts     # NEW
    └── src/components/
        └── live/
            ├── LiveChatInterface.tsx     # NEW
            └── AudioVisualizer.tsx       # NEW
```

### 変更ファイル

```
backend/
├── api/app.py                            # MODIFY: Ephemeralトークンエンドポイント追加
├── agents/hera/adk_hera_agent.py         # MODIFY: Live API対応
├── requirements.txt                      # MODIFY: 依存関係追加
└── .env.example                          # MODIFY: 環境変数追加

frontend/
└── package.json                          # MODIFY: 依存関係追加
```

---

## 🔧 トラブルシューティング

### Q: WebSocket接続が失敗する

**A**: 以下を確認してください：
1. `GEMINI_API_KEY`が正しく設定されているか
2. Ephemeralトークンが正しく生成されているか
3. ファイアウォールがWebSocket接続をブロックしていないか

```bash
# デバッグモードで実行
FLASK_DEBUG=True python api/app.py
```

### Q: 音声が聞こえない

**A**: 以下を確認してください：
1. ブラウザがマイクアクセスを許可しているか
2. 音声フォーマット（16kHz PCM）が正しいか
3. AudioPlayerが正しく初期化されているか

```typescript
// ブラウザコンソールでチェック
console.log(audioPlayer.getState());
```

### Q: 音声遅延が大きい

**A**: 以下を最適化してください：
1. `AUDIO_CHUNK_SIZE_MS`を調整（デフォルト: 100ms）
2. WebSocket接続の安定性を確認
3. サーバーとクライアント間のネットワーク遅延を測定

---

## 📚 参考リソース

### ドキュメント
- [コンテキスト圧縮ドキュメント](GEMINI_LIVE_API_CONTEXT_SUMMARY.md) - プロジェクト全体像
- [詳細実装計画](GEMINI_LIVE_API_INTEGRATION_PLAN.md) - フェーズ別詳細
- [Gemini Live API公式ドキュメント](https://ai.google.dev/gemini-api/docs/live)

### GitHub実装例
- [Google公式デモ](https://github.com/GoogleCloudPlatform/generative-ai/tree/main/gemini/multimodal-live-api/websocket-demo-app)
- [live-api-web-console](https://github.com/google-gemini/live-api-web-console)

---

## ✅ 完了チェックリスト

### 今週のタスク
- [ ] 環境準備完了
- [ ] EphemeralTokenManager実装完了
- [ ] WebSocket接続テスト成功

### 今月のゴール
- [ ] 音声I/O実装完了
- [ ] UI実装完了
- [ ] 基本的な音声チャット機能が動作

---

**準備完了！今すぐ実装を始めましょう！🚀**

**質問・サポートが必要な場合**:
- 詳細実装計画を参照: `GEMINI_LIVE_API_INTEGRATION_PLAN.md`
- プロジェクト全体像を確認: `GEMINI_LIVE_API_CONTEXT_SUMMARY.md`
