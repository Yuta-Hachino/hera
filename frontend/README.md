# AIファミリー・シミュレーター フロントエンド

React (Next.js) + Live2D統合のフロントエンドアプリケーション

## 📋 概要

AIエージェント「ヘーラー（Hera）」との対話を通じて、未来の家族を体験するWebアプリケーションのフロントエンド部分です。

### 主な機能

- ✨ **Live2Dアバター**: ヘーラーのLive2Dアバターが表示され、音声に合わせてリップシンク
- 💬 **リアルタイム対話**: バックエンドAPIと連携したチャット機能
- 📊 **進捗可視化**: 情報収集の進捗をリアルタイムで表示
- 🎤 **音声合成**: Web Speech APIによる日本語音声合成（TTS）
- 📱 **レスポンシブ**: Tailwind CSSによる美しいUI

## 🛠️ 技術スタック

- **フレームワーク**: Next.js 14 (App Router)
- **言語**: TypeScript
- **スタイリング**: Tailwind CSS
- **Live2D**: react-live2d-lipsync
- **状態管理**: React Hooks
- **HTTP通信**: Fetch API

## 📂 プロジェクト構造

```
frontend/
├── app/                      # Next.js App Router
│   ├── page.tsx              # ホーム画面
│   ├── chat/[sessionId]/     # ヒアリング画面
│   ├── complete/[sessionId]/ # 完了画面
│   └── globals.css           # グローバルスタイル
├── components/               # Reactコンポーネント
│   ├── HeraAvatar.tsx        # Live2Dアバター
│   ├── AvatarLayout.tsx      # アバター付きレイアウト
│   ├── ChatMessage.tsx       # チャットメッセージ
│   ├── ChatInput.tsx         # メッセージ入力
│   ├── ProfileProgress.tsx   # 進捗バー
│   └── LoadingSpinner.tsx    # ローディングUI
├── hooks/                    # カスタムフック
│   └── useTTS.ts             # Text-to-Speech制御
├── lib/                      # ユーティリティ
│   ├── api.ts                # API通信関数
│   └── types.ts              # TypeScript型定義
├── public/                   # 静的ファイル
│   └── live2d/               # Live2Dモデル（要配置）
│       └── hera/
│           ├── hera.model3.json
│           ├── hera.moc3
│           └── textures/
└── package.json
```

## 🚀 セットアップ

### 1. 依存関係のインストール

```bash
cd frontend
npm install
```

### 2. Live2Dモデルの配置

**重要**: Live2Dモデルファイルを配置してください。

```
public/
└── live2d/
    └── hera/
        ├── hera.model3.json    # モデル定義ファイル
        ├── hera.moc3            # モデルデータ
        ├── hera.physics3.json   # 物理演算設定
        └── textures/
            └── texture_00.png   # テクスチャ画像
```

**必須パラメータ**:
- `ParamMouthOpenY` - リップシンク用
- `ParamEyeLOpen` - 左目のまばたき
- `ParamEyeROpen` - 右目のまばたき

### 3. 環境変数の設定

`.env.local`ファイルが自動作成されています。バックエンドAPIのURLを確認してください。

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8080
```

### 4. 開発サーバーの起動

```bash
npm run dev
```

ブラウザで http://localhost:3000 にアクセス

## 📝 使用方法

### 1. ホーム画面

- 「体験を始める」ボタンをクリック
- バックエンドAPIにセッションを作成
- ヒアリング画面へ自動遷移

### 2. ヒアリング画面

- 左側にヘーラーのLive2Dアバターが表示
- 右側でチャット形式の対話
- メッセージ送信後、ヘーラーが音声で応答（リップシンク）
- 情報収集進捗が画面上部に表示
- 必須情報が揃うと「完了」ボタンが表示

### 3. 完了画面

- 収集した情報のサマリーを表示
- 「確認して完了する」でセッション完了
- 「戻って修正する」でヒアリング画面に戻る

## 🔌 API連携

### 利用するエンドポイント

| エンドポイント | メソッド | 用途 |
|---------------|---------|------|
| `/api/sessions` | POST | セッション作成 |
| `/api/sessions/{id}/messages` | POST | メッセージ送信 |
| `/api/sessions/{id}/status` | GET | 状態確認 |
| `/api/sessions/{id}/complete` | POST | セッション完了 |

詳細は `lib/api.ts` を参照。

## 🎨 カスタマイズ

### Live2Dモデルの変更

`components/HeraAvatar.tsx` の設定を変更：

```typescript
<Live2DCharacter
  modelPath="/live2d/hera/hera.model3.json"  // モデルパス
  audioVolume={audioVolume}
  positionY={-0.2}                            // Y座標
  scale={1.0}                                 // スケール
  enableBlinking={true}                       // まばたき
  blinkInterval={[3000, 5000]}                // まばたき間隔
  lipSyncSensitivity={1.5}                    // リップシンク感度
/>
```

### テーマカラーの変更

`tailwind.config.js` でカラーパレットを変更：

```javascript
colors: {
  primary: {
    500: '#a855f7',  // メインカラー
    600: '#9333ea',  // ホバー時
    // ...
  },
}
```

### 音声合成の調整

`hooks/useTTS.ts` でTTS設定を変更：

```typescript
utterance.lang = 'ja-JP';  // 言語
utterance.rate = 1.0;       // 速度
utterance.pitch = 1.2;      // ピッチ
utterance.volume = 1.0;     // 音量
```

## 🐛 トラブルシューティング

### Live2Dモデルが表示されない

1. モデルファイルが `public/live2d/hera/` に配置されているか確認
2. `hera.model3.json` のパスが正しいか確認
3. ブラウザのコンソールでエラーを確認

### 音声が再生されない

1. ブラウザがWeb Speech APIに対応しているか確認（Chrome推奨）
2. ページが `localhost` または `https` で動作しているか確認
3. ブラウザの音声設定を確認

### APIとの通信エラー

1. バックエンドサーバーが起動しているか確認（`http://localhost:8080`）
2. `.env.local` の `NEXT_PUBLIC_API_URL` が正しいか確認
3. CORSエラーの場合、バックエンドのCORS設定を確認

## 📦 ビルド

### プロダクションビルド

```bash
npm run build
```

### プロダクション起動

```bash
npm start
```

## 🔒 セキュリティ

- XSS対策: Reactの自動エスケープ機能を活用
- セッションID: URL経由で渡すため、第三者との共有に注意
- 環境変数: `.env.local` はGit管理外（`.gitignore`に記載済み）

## 📄 ライセンス

このプロジェクトはハッカソン用のデモアプリケーションです。

## 🙏 謝辞

- [react-live2d-lipsync](https://github.com/Yuta-Hachino/react-live2d-lipsync) - Live2D統合ライブラリ
- Live2D Cubism - Live2Dモデル形式
- Next.js - Reactフレームワーク
- Tailwind CSS - CSSフレームワーク
