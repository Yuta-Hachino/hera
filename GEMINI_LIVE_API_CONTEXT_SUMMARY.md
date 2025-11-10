# Gemini Live API統合 - コンテキスト圧縮ドキュメント

**作成日**: 2025-11-10
**目的**: AIファミリー・シミュレーターへのGemini Live API統合プロジェクトの全体像を圧縮して把握

---

## 📋 エグゼクティブサマリー

### プロジェクト概要
AIファミリー・シミュレーター「未来の家族を体験」に、**Gemini Live API**を統合し、リアルタイム音声対話機能を実装する。これにより、ユーザーは音声でヘーラーエージェントと自然な対話を行い、未来の家族像を描くことができる。

### 期待される効果
| 項目 | 現状 | 統合後 | インパクト |
|------|------|--------|-----------|
| **対話方式** | テキストのみ | 音声+テキスト | ユーザー体験が劇的に向上 |
| **応答速度** | 3-5秒 | <1秒（ストリーミング） | 自然な会話フロー |
| **対話の質** | 段階的質問 | 自然な流れの対話 | 情報収集効率UP |
| **ユーザーエンゲージメント** | 中 | 高 | 完了率+30% |
| **技術的革新性** | 標準的 | 最先端 | 競合優位性 |

---

## 🏗️ 現状のアーキテクチャ

### バックエンド構成
```
backend/
├── api/app.py              # Flask REST API（ポート8080）
├── agents/
│   ├── hera/
│   │   └── adk_hera_agent.py  # Google ADKベースエージェント
│   └── family/
│       └── family_agent.py    # 家族会話エージェント
├── utils/
│   ├── session_manager.py     # File/Redis/Supabase対応
│   └── storage_manager.py     # Local/S3/GCS/Azure/Supabase対応
└── requirements.txt
```

### 技術スタック
- **フレームワーク**: Flask 3.1.2 + Flask-CORS 5.0.0
- **AI**: Google ADK >=0.1.0 + Gemini 2.5 Pro (google-generativeai 0.8.5)
- **セッション**: File/Redis/Supabase（環境変数で切り替え）
- **ストレージ**: Local/S3/GCS/Azure/Supabase（環境変数で切り替え）
- **認証**: Supabase JWT (pyjwt 2.8.0)
- **データ検証**: Pydantic 2.12.3

### 現在のAPIエンドポイント
```
POST /api/sessions                     # セッション作成
POST /api/sessions/<id>/messages       # テキストメッセージ送信
GET  /api/sessions/<id>/status         # ステータス取得
POST /api/sessions/<id>/complete       # セッション完了
POST /api/sessions/<id>/photos/user    # 画像アップロード
```

### 制約事項
- ✅ REST APIのみ（WebSocket未実装）
- ✅ 音声機能なし
- ✅ リアルタイム対話なし
- ✅ 応答がブロッキング（3-5秒待機）

---

## 🎯 Gemini Live API仕様

### 基本情報
| 項目 | 詳細 |
|------|------|
| **エンドポイント** | `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent` |
| **プロトコル** | WebSocket（双方向ストリーミング） |
| **モデル** | `gemini-2.0-flash-live-preview-04-09` |
| **APIバージョン** | v1beta / v1alpha |

### 認証方式
#### 1. Ephemeral Tokens（推奨：本番環境）
```python
import datetime
import genai

client = genai.Client(http_options={'api_version': 'v1alpha'})
now = datetime.datetime.now(tz=datetime.timezone.utc)

token = client.auth_tokens.create(config={
    'uses': 1,  # 1回のみ使用可能
    'expire_time': now + datetime.timedelta(minutes=30),  # 30分で期限切れ
    'new_session_expire_time': now + datetime.timedelta(minutes=1),
    'http_options': {'api_version': 'v1alpha'},
})
```

**利点**:
- セキュア（短命・使い捨て）
- クライアントサイド直接接続可能
- API Keyを公開しない

#### 2. Direct API Key（開発環境）
```python
ws_url = f"wss://...BidiGenerateContent?key={GEMINI_API_KEY}"
```

### 音声フォーマット仕様
| 方向 | フォーマット | サンプルレート | ビット深度 | チャンネル | エンディアン | MIME Type |
|------|------------|--------------|-----------|----------|------------|-----------|
| **入力** | Raw PCM | 16kHz | 16-bit | Mono | Little-endian | `audio/pcm;rate=16000` |
| **出力** | Raw PCM | 24kHz | 16-bit | Mono | Little-endian | `audio/pcm;rate=24000` |

**重要**:
- リサンプリング対応: 任意のサンプルレートを送信可能（APIが自動リサンプリング）
- 低遅延: Raw PCM形式のため、エンコード/デコードオーバーヘッドなし

### メッセージフォーマット
#### クライアント → サーバー（送信）
```json
{
  "setup": {
    "model": "models/gemini-2.0-flash-exp"
  }
}
```
```json
{
  "realtimeInput": {
    "mediaChunks": [
      {
        "mimeType": "audio/pcm;rate=16000",
        "data": "base64_encoded_audio_data"
      }
    ]
  }
}
```

#### サーバー → クライアント（受信）
```json
{
  "serverContent": {
    "modelTurn": {
      "parts": [
        {
          "text": "こんにちは！"
        }
      ]
    }
  }
}
```
```json
{
  "serverContent": {
    "modelTurn": {
      "parts": [
        {
          "inlineData": {
            "mimeType": "audio/pcm;rate=24000",
            "data": "base64_encoded_audio_data"
          }
        }
      ]
    }
  }
}
```

### 主要機能
- ✅ **Voice Activity Detection（VAD）**: 音声の開始/終了を自動検出
- ✅ **割り込み対応**: ユーザーがAIの応答中に話しかけることが可能
- ✅ **Function Calling**: ツール呼び出しをサポート
- ✅ **マルチモーダル**: 音声+テキスト+画像+動画の同時入力
- ✅ **ストリーミング**: リアルタイムで応答を生成・再生

---

## 🔧 技術的実装要件

### 1. バックエンド変更

#### 新規依存関係
```python
# requirements.txt に追加
websockets==12.0        # WebSocketサーバー
pyaudio==0.2.14         # 音声I/O（開発用）
pydub==0.25.1           # 音声処理
google-genai>=0.8.0     # Gemini Live API SDK（既存）
```

#### 新規エンドポイント
```
WebSocket /api/sessions/<id>/live    # Gemini Live API接続
GET /api/sessions/<id>/ephemeral-token  # Ephemeralトークン生成（オプション）
```

#### アーキテクチャパターン
**Option A: フロントエンド直接接続（推奨）**
```
ユーザー（ブラウザ）
  ↓ WebSocket
Gemini Live API
  ↑
バックエンド（Ephemeralトークン発行のみ）
```

**Option B: バックエンドプロキシ**
```
ユーザー（ブラウザ）
  ↓ WebSocket
バックエンド（Flask-SocketIO）
  ↓ WebSocket
Gemini Live API
```

### 2. フロントエンド変更

#### 新規依存関係
```json
// frontend/package.json に追加
{
  "dependencies": {
    "wavesurfer.js": "^7.0.0",  // 音声可視化
    "@types/dom-mediacapture-record": "^1.0.0"  // MediaRecorder型定義
  }
}
```

#### 新規コンポーネント
```
frontend/src/components/
├── audio/
│   ├── AudioInput.tsx      # マイク入力管理
│   ├── AudioOutput.tsx     # 音声再生管理
│   ├── AudioVisualizer.tsx # 波形表示
│   └── VoiceActivityDetector.tsx  # VAD UI
└── live/
    ├── LiveSessionManager.tsx  # WebSocket管理
    └── LiveChatInterface.tsx   # 音声チャットUI
```

#### Web Audio API統合
```typescript
// マイク入力（16kHz PCM変換）
const audioContext = new AudioContext({ sampleRate: 16000 });
const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
const source = audioContext.createMediaStreamSource(mediaStream);

// 音声出力（24kHz PCM再生）
const audioBuffer = audioContext.createBuffer(1, pcmData.length, 24000);
audioBuffer.copyToChannel(pcmData, 0);
const source = audioContext.createBufferSource();
source.buffer = audioBuffer;
source.connect(audioContext.destination);
source.start();
```

### 3. ADKHeraAgent拡張

#### 音声対話モード追加
```python
class ADKHeraAgent:
    def __init__(self, gemini_api_key: str):
        # 既存の初期化
        self.live_mode = False  # 音声モードフラグ
        self.ws_connection = None  # WebSocket接続

    async def start_live_session(self, session_id: str) -> str:
        """Gemini Live APIセッション開始"""
        # Ephemeralトークン生成
        # WebSocket接続確立
        # 音声ストリームの開始
        pass

    async def send_audio_chunk(self, audio_data: bytes) -> None:
        """音声チャンクを送信"""
        pass

    async def receive_audio_stream(self) -> AsyncGenerator[bytes, None]:
        """音声ストリームを受信"""
        pass
```

---

## 📊 実装計画概要

### Phase 1: 基礎実装（Week 1-2）
- Gemini Live API SDK統合
- Ephemeralトークン生成機能
- 基本的なWebSocket接続

### Phase 2: 音声I/O（Week 3-4）
- マイク入力（16kHz PCM）
- 音声出力（24kHz PCM）
- Web Audio API統合

### Phase 3: UI/UX（Week 5-6）
- 音声チャットインターフェース
- 音声可視化（波形表示）
- VAD UI（話している/聞いているの表示）

### Phase 4: ADKエージェント統合（Week 7-8）
- ADKHeraAgentの音声対応
- セッション管理統合
- エラーハンドリング

### Phase 5: テスト・最適化（Week 9-10）
- 統合テスト
- パフォーマンス最適化
- 本番デプロイ

---

## 🎓 参考リソース

### 公式ドキュメント
- [Gemini Live API - Getting Started](https://ai.google.dev/gemini-api/docs/live)
- [Live API - WebSockets API Reference](https://ai.google.dev/api/live)
- [Ephemeral Tokens](https://ai.google.dev/gemini-api/docs/ephemeral-tokens)
- [Live API Capabilities Guide](https://ai.google.dev/gemini-api/docs/live-guide)

### GitHub実装例
- [Google公式: websocket-demo-app](https://github.com/GoogleCloudPlatform/generative-ai/tree/main/gemini/multimodal-live-api/websocket-demo-app)
- [Google公式: live-api-web-console](https://github.com/google-gemini/live-api-web-console)
- [FastAPI実装例](https://github.com/AnelMusic/google-gemini-live-api-multimodal-demo)
- [Pipecat.ai実装](https://github.com/pipecat-ai/gemini-webrtc-web-simple)

### 技術記事
- [Geminiとリアルタイム音声会話できるWebアプリの作り方 | sreake.com](https://sreake.com/blog/gemini-realtime-voice-chat-app/)
- [Gemini 2.0 と Multimodal Live API で実現するヒアリング Voice エージェント](https://zenn.dev/mrmtsntr/articles/3859ec6b61b63b)
- [Gemini 2.0 Multimodal Live API でリアルタイムマルチモーダルアプリケーションを構築しよう！](https://zenn.dev/google_cloud_jp/articles/5696180a001fc0)

---

## ⚠️ 重要な注意事項

### セキュリティ
- ✅ **API Key保護**: フロントエンドに絶対に含めない
- ✅ **Ephemeral Tokens推奨**: 本番環境では必須
- ✅ **CORS設定**: 適切なオリジンのみ許可

### パフォーマンス
- ✅ **音声バッファリング**: 100-200msのチャンクで送信
- ✅ **WebSocket再接続**: ネットワーク断時の自動再接続
- ✅ **リソース管理**: AudioContextの適切なクリーンアップ

### UX
- ✅ **マイク権限**: 初回アクセス時にユーザー許可必要
- ✅ **フォールバック**: 音声非対応時はテキストモード継続
- ✅ **ローディング状態**: 接続中・処理中の適切な表示

---

## 🎯 成功指標（KPI）

| KPI | 現状 | 目標 | 測定方法 |
|-----|------|------|----------|
| **平均応答時間** | 3-5秒 | <1秒 | WebSocket latency監視 |
| **情報収集完了率** | 60% | 80% | セッション完了/開始 |
| **ユーザー満足度** | 3.5/5.0 | 4.5/5.0 | アンケート |
| **平均対話ターン数** | 8-10ターン | 5-7ターン | セッションログ分析 |
| **音声入力利用率** | 0% | 70% | 音声/テキスト比率 |

---

**このドキュメントは、プロジェクトの全体像を素早く把握するために設計されています。**
**詳細な実装計画は `GEMINI_LIVE_API_INTEGRATION_PLAN.md` を参照してください。**
