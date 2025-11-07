# メール送信機能のセットアップガイド

このガイドでは、お問い合わせフォームから実際にメールを送信するための設定方法を説明します。

## 現在の状態

現在、お問い合わせフォームは動作していますが、実際のメール送信は行われず、コンソールログに内容が出力されるだけです。

## 実際にメールを送信する方法

実際のメール送信を実装するには、以下のいずれかの方法を選択してください。

### オプション1: Gmail SMTP（簡易的な方法）

#### 1. 必要なパッケージをインストール

```bash
npm install nodemailer
npm install --save-dev @types/nodemailer
```

#### 2. Googleアカウントでアプリパスワードを生成

1. Googleアカウントにログイン
2. [アプリパスワード](https://myaccount.google.com/apppasswords)にアクセス
3. 新しいアプリパスワードを生成
4. パスワードをコピー

#### 3. 環境変数を設定

`.env.local`ファイルを作成し、以下を追加：

```bash
EMAIL_USER=hera.ai.contact@gmail.com
EMAIL_PASSWORD=生成したアプリパスワード
```

#### 4. APIルートを更新

`app/api/contact/route.ts`の該当部分のコメントを解除し、nodemailerの実装を有効化してください。

### オプション2: SendGrid（推奨）

SendGridは無料プランで1日100通まで送信可能です。

#### 1. SendGridアカウントを作成

[SendGrid](https://sendgrid.com/)にアクセスし、無料アカウントを作成

#### 2. APIキーを生成

1. SendGridダッシュボードにログイン
2. Settings > API Keys
3. Create API Key
4. Full Accessで作成
5. APIキーをコピー

#### 3. 必要なパッケージをインストール

```bash
npm install @sendgrid/mail
```

#### 4. 環境変数を設定

`.env.local`ファイルに以下を追加：

```bash
SENDGRID_API_KEY=あなたのAPIキー
```

#### 5. APIルートを更新

`app/api/contact/route.ts`を以下のように変更：

```typescript
import { NextRequest, NextResponse } from 'next/server'
import sgMail from '@sendgrid/mail'

sgMail.setApiKey(process.env.SENDGRID_API_KEY!)

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { name, email, subject, message } = body

    // バリデーション
    if (!name || !email || !subject || !message) {
      return NextResponse.json(
        { error: '必須項目が入力されていません' },
        { status: 400 }
      )
    }

    const msg = {
      to: 'hera.ai.contact@gmail.com',
      from: 'hera.ai.contact@gmail.com', // SendGridで認証済みのメールアドレス
      replyTo: email,
      subject: `[お問い合わせ] ${subject}`,
      text: `
お名前: ${name}
メールアドレス: ${email}
件名: ${subject}

お問い合わせ内容:
${message}
      `,
      html: `
<h2>お問い合わせフォーム送信</h2>
<p><strong>お名前:</strong> ${name}</p>
<p><strong>メールアドレス:</strong> ${email}</p>
<p><strong>件名:</strong> ${subject}</p>
<h3>お問い合わせ内容:</h3>
<p>${message.replace(/\n/g, '<br>')}</p>
      `,
    }

    await sgMail.send(msg)

    return NextResponse.json(
      {
        success: true,
        message: 'お問い合わせを受け付けました。ご連絡ありがとうございます。',
      },
      { status: 200 }
    )
  } catch (error) {
    console.error('お問い合わせフォームエラー:', error)
    return NextResponse.json(
      { error: 'サーバーエラーが発生しました' },
      { status: 500 }
    )
  }
}
```

### オプション3: Resend（最新のおすすめ）

Resendは開発者フレンドリーなメール送信サービスです。

#### 1. Resendアカウントを作成

[Resend](https://resend.com/)にアクセスし、無料アカウントを作成

#### 2. APIキーを生成

1. Resendダッシュボードにログイン
2. API Keysセクション
3. Create API Key
4. APIキーをコピー

#### 3. 必要なパッケージをインストール

```bash
npm install resend
```

#### 4. 環境変数を設定

`.env.local`ファイルに以下を追加：

```bash
RESEND_API_KEY=あなたのAPIキー
```

#### 5. APIルートを更新

```typescript
import { NextRequest, NextResponse } from 'next/server'
import { Resend } from 'resend'

const resend = new Resend(process.env.RESEND_API_KEY)

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { name, email, subject, message } = body

    // バリデーション
    if (!name || !email || !subject || !message) {
      return NextResponse.json(
        { error: '必須項目が入力されていません' },
        { status: 400 }
      )
    }

    const { data, error } = await resend.emails.send({
      from: 'onboarding@resend.dev', // Resendのデフォルト送信元
      to: ['hera.ai.contact@gmail.com'],
      replyTo: email,
      subject: `[お問い合わせ] ${subject}`,
      html: `
<h2>お問い合わせフォーム送信</h2>
<p><strong>お名前:</strong> ${name}</p>
<p><strong>メールアドレス:</strong> ${email}</p>
<p><strong>件名:</strong> ${subject}</p>
<h3>お問い合わせ内容:</h3>
<p>${message.replace(/\n/g, '<br>')}</p>
      `,
    })

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 400 })
    }

    return NextResponse.json(
      {
        success: true,
        message: 'お問い合わせを受け付けました。ご連絡ありがとうございます。',
      },
      { status: 200 }
    )
  } catch (error) {
    console.error('お問い合わせフォームエラー:', error)
    return NextResponse.json(
      { error: 'サーバーエラーが発生しました' },
      { status: 500 }
    )
  }
}
```

## 本番環境での設定

本番環境にデプロイする際は、Vercelなどの環境変数設定画面で同じ環境変数を設定してください。

### Vercelの場合

1. Vercelダッシュボード
2. プロジェクトを選択
3. Settings > Environment Variables
4. 環境変数を追加

## セキュリティ上の注意

- `.env.local`ファイルは`.gitignore`に含めてください（既に含まれています）
- APIキーやパスワードは絶対にGitにコミットしないでください
- 本番環境では必ずレート制限を設定してください

## トラブルシューティング

### メールが届かない場合

1. スパムフォルダを確認
2. SendGrid/Resendのダッシュボードでログを確認
3. APIキーが正しく設定されているか確認
4. 環境変数が正しく読み込まれているか確認（`console.log`で確認）

### Gmailでエラーが出る場合

- 2段階認証が有効になっているか確認
- アプリパスワードが正しく生成されているか確認
- セキュリティ設定で「安全性の低いアプリ」が許可されているか確認
