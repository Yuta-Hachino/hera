# 日本語音声合成サービス比較調査

AIファミリー・シミュレーターでの使用を想定した、日本語音声合成（TTS）サービスの比較調査結果です。

## 📊 総合比較表

| サービス | 品質 | 価格 | 日本語品質 | 実装難易度 | 無料枠 | おすすめ度 |
|---------|------|------|-----------|-----------|--------|----------|
| **OpenAI TTS** | ⭐️⭐️⭐️⭐️⭐️ | $15-30/1M | ⭐️⭐️⭐️⭐️⭐️ | 簡単 | なし | ⭐️⭐️⭐️⭐️⭐️ |
| **ElevenLabs** | ⭐️⭐️⭐️⭐️⭐️ | $5-99/月 | ⭐️⭐️⭐️⭐️⭐️ | 簡単 | 10,000文字/月 | ⭐️⭐️⭐️⭐️⭐️ |
| **Google Cloud TTS** | ⭐️⭐️⭐️⭐️⭐️ | $4-16/1M | ⭐️⭐️⭐️⭐️⭐️ | 普通 | 400万文字/月 | ⭐️⭐️⭐️⭐️⭐️ |
| **Azure Speech** | ⭐️⭐️⭐️⭐️ | $16/1M | ⭐️⭐️⭐️⭐️⭐️ | 普通 | 50万文字/月 | ⭐️⭐️⭐️⭐️ |
| **Amazon Polly** | ⭐️⭐️⭐️⭐️ | $16/1M | ⭐️⭐️⭐️⭐️ | 普通 | 500万文字/月 | ⭐️⭐️⭐️⭐️ |
| **VOICEVOX** | ⭐️⭐️⭐️ | 無料 | ⭐️⭐️⭐️⭐️ | やや難 | 無制限 | ⭐️⭐️⭐️⭐️ |
| **COEIROINK** | ⭐️⭐️⭐️⭐️ | 無料 | ⭐️⭐️⭐️⭐️ | やや難 | 無制限 | ⭐️⭐️⭐️⭐️ |
| **Style-Bert-VITS2** | ⭐️⭐️⭐️⭐️⭐️ | 無料 | ⭐️⭐️⭐️⭐️⭐️ | 難 | 無制限 | ⭐️⭐️⭐️⭐️ |
| **CoeFont** | ⭐️⭐️⭐️⭐️ | ¥980-4980/月 | ⭐️⭐️⭐️⭐️ | 簡単 | 3,000文字/月 | ⭐️⭐️⭐️ |
| **SHAREVOX** | ⭐️⭐️⭐️ | 無料 | ⭐️⭐️⭐️⭐️ | やや難 | 無制限 | ⭐️⭐️⭐️ |
| **IBM Watson** | ⭐️⭐️⭐️⭐️ | $20/1M | ⭐️⭐️⭐️ | 普通 | 10,000文字/月 | ⭐️⭐️⭐️ |
| **CeVIO AI** | ⭐️⭐️⭐️⭐️⭐️ | ¥8,000~ | ⭐️⭐️⭐️⭐️⭐️ | 普通 | - | ⭐️⭐️⭐️ |
| **A.I.VOICE** | ⭐️⭐️⭐️⭐️⭐️ | ¥6,578~ | ⭐️⭐️⭐️⭐️⭐️ | 普通 | - | ⭐️⭐️⭐️ |
| **ReadSpeaker** | ⭐️⭐️⭐️⭐️ | 要見積もり | ⭐️⭐️⭐️⭐️ | 普通 | - | ⭐️⭐️ |
| **Koemotion** | ⭐️⭐️⭐️ | 無料 | ⭐️⭐️⭐️ | 難 | 無制限 | ⭐️⭐️ |

---

## 🔍 各サービス詳細

### 1. OpenAI TTS ⭐️ コスパ最高

**特徴**
- 非常に自然で人間らしい音声
- 感情表現が豊か
- レイテンシが低い
- 実装が簡単

**音声サンプル**
- 6種類の声: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`
- モデル: `tts-1`（標準）、`tts-1-hd`（高品質）

**価格**
- tts-1: $15.00 / 1M文字
- tts-1-hd: $30.00 / 1M文字

**実装例**
```typescript
import OpenAI from 'openai'

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY })

const mp3 = await openai.audio.speech.create({
  model: "tts-1-hd",
  voice: "nova",
  input: "こんにちは、未来の家族へようこそ",
  response_format: "mp3",
  speed: 1.0
})
```

**試聴URL**
- 公式ドキュメント: https://platform.openai.com/docs/guides/text-to-speech

**おすすめ度**: ⭐️⭐️⭐️⭐️⭐️

---

### 2. ElevenLabs ⭐️ 最高品質

**特徴**
- 業界最高レベルの自然さ
- 感情・イントネーションが非常にリアル
- 声のクローニングが可能
- 多言語対応（日本語も高品質）

**価格**
- Free: 10,000文字/月
- Starter: $5/月（30,000文字）
- Creator: $22/月（100,000文字）
- Pro: $99/月（500,000文字）

**実装例**
```typescript
const response = await fetch(
  'https://api.elevenlabs.io/v1/text-to-speech/voice_id',
  {
    method: 'POST',
    headers: {
      'xi-api-key': process.env.ELEVENLABS_API_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text: "こんにちは、未来の家族へようこそ",
      model_id: "eleven_multilingual_v2",
      voice_settings: {
        stability: 0.5,
        similarity_boost: 0.75,
      },
    }),
  }
)
```

**試聴URL**
- 公式デモ: https://elevenlabs.io/
- Voice Library: https://elevenlabs.io/voice-library
- 日本語サンプル: https://elevenlabs.io/languages/japanese-text-to-speech

**おすすめ度**: ⭐️⭐️⭐️⭐️⭐️

---

### 3. Google Cloud Text-to-Speech ⭐️ 無料枠最大

**特徴**
- Google提供の高品質TTS
- Wavenet/Neural2は非常に自然
- 無料枠が非常に大きい（400万文字/月）
- 日本語の声が豊富

**日本語の声**
- `ja-JP-Wavenet-A`, `ja-JP-Wavenet-B`, `ja-JP-Wavenet-C`, `ja-JP-Wavenet-D`
- `ja-JP-Neural2-B`, `ja-JP-Neural2-C`, `ja-JP-Neural2-D`

**価格**
- Standard: $4 / 1M文字
- Wavenet: $16 / 1M文字
- Neural2: $16 / 1M文字
- 無料枠: 400万文字/月（Standard）、100万文字/月（Wavenet/Neural2）

**実装例**
```typescript
import textToSpeech from '@google-cloud/text-to-speech'

const client = new textToSpeech.TextToSpeechClient()
const [response] = await client.synthesizeSpeech({
  input: { text: 'こんにちは' },
  voice: { languageCode: 'ja-JP', name: 'ja-JP-Neural2-B' },
  audioConfig: { audioEncoding: 'MP3' },
})
```

**試聴URL**
- 公式デモ: https://cloud.google.com/text-to-speech?hl=ja#demo
- 日本語音声一覧: https://cloud.google.com/text-to-speech/docs/voices?hl=ja

**おすすめ度**: ⭐️⭐️⭐️⭐️⭐️

---

### 4. Azure Speech Services (Neural Voices)

**特徴**
- Microsoft提供、エンタープライズレベル
- 日本語の品質が非常に高い
- 多様な声の選択肢
- SSML対応

**日本語の声**
- `ja-JP-NanamiNeural`（女性）- 明るく親しみやすい
- `ja-JP-KeitaNeural`（男性）- 落ち着いた声
- `ja-JP-AoiNeural`（女性・子供）
- `ja-JP-ShioriNeural`（女性）- 優しい声

**価格**
- Neural Voices: $16 / 1M文字
- 無料枠: 500,000文字/月（最初の12ヶ月）

**試聴URL**
- 公式デモ: https://azure.microsoft.com/ja-jp/products/cognitive-services/text-to-speech/
- Voice Gallery: https://speech.microsoft.com/portal/voicegallery

**おすすめ度**: ⭐️⭐️⭐️⭐️

---

### 5. Amazon Polly (Neural)

**特徴**
- AWS提供、信頼性が高い
- Neural voicesで自然な音声
- 日本語対応

**日本語の声**
- `Takumi`（男性）
- `Kazuha`（女性）

**価格**
- Neural: $16 / 1M文字
- Standard: $4 / 1M文字
- 無料枠: 500万文字/月（最初の12ヶ月）

**試聴URL**
- 公式デモ: https://us-east-1.console.aws.amazon.com/polly/home/SynthesizeSpeech
- 日本語音声サンプル: https://docs.aws.amazon.com/polly/latest/dg/voicelist.html

**おすすめ度**: ⭐️⭐️⭐️⭐️

---

### 6. VOICEVOX 🆓 無料・キャラクター声

**特徴**
- 完全無料（オープンソース）
- 日本語専用、高品質
- キャラクター音声（アニメ・ゲーム風）
- ローカルで動作可能
- Dockerで簡単に起動

**価格**: 無料

**実装例**
```bash
# Dockerで起動
docker pull voicevox/voicevox_engine:cpu-ubuntu20.04-latest
docker run --rm -p 50021:50021 voicevox/voicevox_engine:cpu-ubuntu20.04-latest
```

```typescript
// API呼び出し
const response = await fetch(
  'http://localhost:50021/audio_query?text=こんにちは&speaker=1',
  { method: 'POST' }
)
const query = await response.json()

const audio = await fetch(
  'http://localhost:50021/synthesis?speaker=1',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(query),
  }
)
```

**試聴URL**
- 公式サイト: https://voicevox.hiroshiba.jp/
- オンラインデモ: https://voicevox.su-shiki.com/
- YouTube紹介動画: https://www.youtube.com/watch?v=4yVpklclxwU

**おすすめ度**: ⭐️⭐️⭐️⭐️

---

### 7. COEIROINK 🆓

**特徴**
- VOICEVOXの派生プロジェクト
- 完全無料・オープンソース
- より自然な日本語音声
- ローカルで動作

**価格**: 無料

**試聴URL**
- 公式サイト: https://coeiroink.com/
- サンプル音声: https://coeiroink.com/sample
- YouTube: https://www.youtube.com/watch?v=PlJw85mJAVk

**おすすめ度**: ⭐️⭐️⭐️⭐️

---

### 8. Style-Bert-VITS2 🆓 超高品質

**特徴**
- オープンソース
- 非常に自然な音声
- 感情表現が豊か
- 自分で学習モデルを作成可能

**価格**: 無料（自己ホスティング）

**試聴URL**
- デモページ: https://huggingface.co/spaces/litagin/Style-Bert-VITS2-Editor-Demo
- サンプル音声集: https://github.com/litagin02/Style-Bert-VITS2/wiki/Sample-audios
- GitHub: https://github.com/litagin02/Style-Bert-VITS2

**おすすめ度**: ⭐️⭐️⭐️⭐️

---

### 9. CoeFont 🇯🇵

**特徴**
- 日本企業のサービス
- 日本語特化
- キャラクター音声も豊富
- 商用利用可能

**価格**
- Free: 月3,000文字
- Lite: ¥980/月（30,000文字）
- Standard: ¥4,980/月（200,000文字）

**試聴URL**
- 公式デモ: https://coefont.cloud/
- Voice Library: https://coefont.cloud/coefonts
- サンプル動画: https://www.youtube.com/watch?v=hQqH0KGzUr4

**おすすめ度**: ⭐️⭐️⭐️

---

### 10. SHAREVOX 🆓

**特徴**
- VOICEVOXの派生
- 完全無料
- オープンソース
- キャラクター音声

**価格**: 無料

**試聴URL**
- 公式サイト: https://www.sharevox.app/
- オンラインデモ: https://w.sharevox.app/
- YouTube: https://www.youtube.com/watch?v=oJTfLRlTy1Y

**おすすめ度**: ⭐️⭐️⭐️

---

### 11. IBM Watson Text to Speech

**特徴**
- エンタープライズ向けだが個人でも使える
- 日本語対応
- カスタマイズ可能

**価格**
- $0.02 / 1,000文字（約$20/1M文字）
- Lite: 10,000文字/月 無料

**試聴URL**
- 公式デモ: https://www.ibm.com/demos/live/tts-demo/self-service/home
- 日本語音声サンプル: https://cloud.ibm.com/docs/text-to-speech?topic=text-to-speech-voices

**おすすめ度**: ⭐️⭐️⭐️

---

### 12. CeVIO AI 💰

**特徴**
- 日本製の高品質TTS
- アニメ・ゲーム向けのキャラクター声
- オフライン動作
- 買い切り型

**価格**: ソフトウェア購入（¥8,000〜）

**試聴URL**
- 公式サイト: https://cevio.jp/
- 公式サンプル: https://cevio.jp/product/cta/
- 体験版ダウンロード: https://cevio.jp/trial/

**おすすめ度**: ⭐️⭐️⭐️

---

### 13. A.I.VOICE 💰

**特徴**
- 日本製の高品質TTS
- 感情表現が豊か
- 商用利用可能
- オフライン動作

**価格**: ソフトウェア購入（¥6,578〜）

**試聴URL**
- 公式サイト: https://aivoice.jp/
- サンプル音声: https://aivoice.jp/product/
- YouTube: https://www.youtube.com/watch?v=qN4ooNx77u0

**おすすめ度**: ⭐️⭐️⭐️

---

### 14. ReadSpeaker 💰

**特徴**
- 商用利用に強い
- 日本語の品質が高い
- 企業向け

**価格**: 従量課金（見積もり必要）

**試聴URL**
- 公式デモ: https://www.readspeaker.com/ja/demo/
- 日本語サンプル: https://www.readspeaker.com/ja/

**おすすめ度**: ⭐️⭐️

---

### 15. Koemotion 🆓

**特徴**
- リアルタイム音声変換
- 感情表現が可能
- オープンソース
- ローカルで動作

**価格**: 無料

**試聴URL**
- GitHub: https://github.com/rinna/koemotion
- デモ動画: https://www.youtube.com/watch?v=9hboWTeNVi4

**おすすめ度**: ⭐️⭐️

---

## 💡 用途別おすすめ

### 🥇 完全無料で試したい
1. **VOICEVOX** - 最も有名、コミュニティ大きい、Dockerで簡単起動
2. **COEIROINK** - VOICEVOXより自然
3. **Style-Bert-VITS2** - 最高品質、セットアップやや難
4. **SHAREVOX** - VOICEVOX互換

### 🥈 低コスト・従量課金
1. **Google Cloud TTS (Standard)** - $4/1M文字、無料枠400万文字/月
2. **OpenAI TTS** - $15/1M文字、実装簡単、品質高い
3. **Azure Speech** - $16/1M文字、無料枠50万文字/月
4. **Amazon Polly** - $16/1M文字、無料枠500万文字/月

### 🥉 最高品質重視
1. **ElevenLabs** - 業界最高レベル、$5/月〜
2. **Style-Bert-VITS2** - 無料だが高品質、セットアップ必要
3. **OpenAI TTS HD** - $30/1M文字、実装簡単
4. **CeVIO AI** - 買い切り、日本製

### 🎯 キャラクター声
1. **VOICEVOX** - 無料、人気、豊富な声
2. **COEIROINK** - 無料、自然
3. **CoeFont** - 有料、商用可能
4. **SHAREVOX** - 無料、VOICEVOX互換

---

## 🚀 このアプリに最適な組み合わせ案

### パターン1: 完全無料（開発・テスト向け）
```
VOICEVOX（メインキャラクター） + COEIROINK（サブキャラクター）
```
- **コスト**: ¥0
- **品質**: ⭐️⭐️⭐️⭐️
- **セットアップ**: Docker 1コマンドで完了
- **メリット**: 完全無料、キャラクター性が高い
- **デメリット**: サーバーリソース必要、自然さはやや劣る

### パターン2: 低コスト・高品質（本番推奨）
```
Google Cloud TTS (Standard) 無料枠内
```
- **コスト**: 月400万文字まで無料（超過後 $4/1M）
- **品質**: ⭐️⭐️⭐️⭐️⭐️
- **セットアップ**: やや複雑（GCPアカウント必要）
- **メリット**: 大規模な無料枠、高品質
- **デメリット**: GCP設定が必要

### パターン3: バランス型（開発〜本番）
```
OpenAI TTS
```
- **コスト**: 月1万回再生（100文字/回）でも約$15
- **品質**: ⭐️⭐️⭐️⭐️⭐️
- **セットアップ**: 超簡単（APIキー1つ）
- **メリット**: 実装が簡単、品質が高い、既存のOpenAI統合
- **デメリット**: 無料枠なし

### パターン4: 超高品質（プレミアム）
```
ElevenLabs
```
- **コスト**: $5/月（30,000文字）
- **品質**: ⭐️⭐️⭐️⭐️⭐️（最高）
- **セットアップ**: 簡単
- **メリット**: 業界最高品質、感情表現豊か
- **デメリット**: やや高価

---

## 🎯 最終推奨

このアプリ（AIファミリー・シミュレーター）の用途を考えると：

### 開発段階
**VOICEVOX**
- 理由: 無料、すぐ使える、キャラクター性が家族シミュレーターに合う
- Docker 1コマンドで起動可能

### 本番環境（少数ユーザー）
**OpenAI TTS**
- 理由: コスパ最高、実装簡単、高品質
- 既にGemini APIを使っているなら統合しやすい

### 本番環境（多数ユーザー）
**Google Cloud TTS Standard**
- 理由: 無料枠が大きい（月400万文字）
- 品質も十分高い

---

## 📝 実装時のポイント

### チェックリスト
- [ ] 試聴して音声の品質を確認
- [ ] コスト試算（予想使用量から計算）
- [ ] 実装難易度の確認
- [ ] レイテンシのテスト
- [ ] ライセンス・利用規約の確認
- [ ] 商用利用の可否確認

### 比較のポイント
1. **自然さ**: 人間らしい話し方か
2. **イントネーション**: 日本語のアクセントが正しいか
3. **感情表現**: 抑揚があるか
4. **声の種類**: 複数の声から選べるか
5. **レイテンシ**: 生成速度は速いか
6. **コスト**: 予算内に収まるか

---

## 🔗 すぐに試せるデモURL（登録不要）

1. **Google Cloud TTS**: https://cloud.google.com/text-to-speech?hl=ja#demo
2. **VOICEVOX オンライン**: https://voicevox.su-shiki.com/
3. **Azure Speech Demo**: https://azure.microsoft.com/ja-jp/products/cognitive-services/text-to-speech/
4. **CoeFont**: https://coefont.cloud/

---

**調査日**: 2025年1月
**対象用途**: AIファミリー・シミュレーター
**評価基準**: 日本語品質、コスト、実装難易度、使いやすさ
