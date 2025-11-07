# SendGrid セットアップガイド（簡易版）

お問い合わせフォームから実際にメールを送信するための設定方法です。

## 手順

### 1. SendGridアカウント作成（無料）

1. [SendGrid](https://signup.sendgrid.com/)にアクセス
2. 無料アカウントを作成
   - 無料プラン: 1日100通まで送信可能
   - クレジットカード不要

### 2. APIキーの生成

1. SendGridにログイン
2. 左メニューから **Settings** → **API Keys** を選択
3. **Create API Key** をクリック
4. API Key Name: `Hera Contact Form` など（任意）
5. API Key Permissions: **Full Access** を選択
6. **Create & View** をクリック
7. **APIキーをコピー**（このAPIキーは一度しか表示されません！）

### 3. 送信元メールアドレスの認証

SendGridでメールを送信するには、送信元アドレス（hera.ai.contact@gmail.com）を認証する必要があります。

#### 方法1: Single Sender Verification（簡単、推奨）

1. SendGridダッシュボードで **Settings** → **Sender Authentication** を選択
2. **Verify a Single Sender** をクリック
3. 以下を入力:
   - From Name: `Heraチーム`
   - From Email Address: `hera.ai.contact@gmail.com`
   - Reply To: `hera.ai.contact@gmail.com`
   - 会社名、住所などの情報を入力
4. **Create** をクリック
5. hera.ai.contact@gmail.comに送られた認証メールを確認
6. **Verify Single Sender** をクリック

### 4. 環境変数の設定

プロジェクトルート（frontendディレクトリ）に`.env.local`ファイルを作成または編集:

```bash
# .env.local
SENDGRID_API_KEY=手順2でコピーしたAPIキー
```

**重要**: `.env.local`ファイルは`.gitignore`に含まれているため、Gitにコミットされません。

### 5. 開発サーバーの再起動

環境変数を読み込むため、開発サーバーを再起動:

```bash
# Ctrl+Cで停止してから
npm run dev
```

### 6. テスト送信

1. http://localhost:3000/contact にアクセス
2. お問い合わせフォームに入力して送信
3. hera.ai.contact@gmail.comにメールが届くことを確認

## トラブルシューティング

### メールが届かない場合

1. **SendGrid Activity Feedを確認**
   - SendGridダッシュボード → **Activity** → **Activity Feed**
   - メールの送信状況を確認

2. **スパムフォルダを確認**
   - Gmailのスパムフォルダを確認

3. **認証状態を確認**
   - Settings → Sender Authentication で認証済みか確認

4. **APIキーの権限を確認**
   - Settings → API Keys でFull Accessになっているか確認

5. **コンソールログを確認**
   - ターミナルでエラーメッセージを確認

### APIキーが設定されていない場合

APIキーが設定されていない場合でも、フォームは動作します。
その場合、実際のメール送信はスキップされ、コンソールログに内容が出力されます（テストモード）。

## 本番環境（Vercel）での設定

Vercelにデプロイする場合:

1. Vercelダッシュボードを開く
2. プロジェクトを選択
3. **Settings** → **Environment Variables**
4. 以下を追加:
   - Key: `SENDGRID_API_KEY`
   - Value: SendGridのAPIキー
5. **Save** をクリック
6. 再デプロイ

## コスト

- **無料プラン**: 1日100通まで
- 超過する場合: 有料プランへのアップグレードが必要
  - Essentials: $19.95/月（50,000通/月）
  - Pro: $89.95/月（100,000通/月）

通常のお問い合わせフォームであれば、無料プランで十分です。

## サポート

問題が解決しない場合は、SendGridの[公式ドキュメント](https://docs.sendgrid.com/)を参照してください。
