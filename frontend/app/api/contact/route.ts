import { NextRequest, NextResponse } from 'next/server'
import sgMail from '@sendgrid/mail'

/**
 * お問い合わせフォームAPIエンドポイント
 * POST /api/contact
 *
 * SendGridを使用してメールを送信します
 */

// SendGrid APIキーの設定
if (process.env.SENDGRID_API_KEY) {
  sgMail.setApiKey(process.env.SENDGRID_API_KEY)
}

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

    // メールアドレスの形式チェック
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      return NextResponse.json(
        { error: 'メールアドレスの形式が正しくありません' },
        { status: 400 }
      )
    }

    // SendGrid APIキーが設定されていない場合は、コンソールログのみ
    if (!process.env.SENDGRID_API_KEY) {
      console.log('========== お問い合わせフォーム送信（テストモード） ==========')
      console.log('送信日時:', new Date().toLocaleString('ja-JP'))
      console.log('お名前:', name)
      console.log('メールアドレス:', email)
      console.log('件名:', subject)
      console.log('内容:', message)
      console.log('送信先: hera.ai.contact@gmail.com')
      console.log('⚠️  SENDGRID_API_KEYが設定されていないため、実際のメール送信はスキップされました')
      console.log('===========================================')

      return NextResponse.json(
        {
          success: true,
          message: 'お問い合わせを受け付けました（テストモード）',
        },
        { status: 200 }
      )
    }

    // SendGridでメール送信
    const msg = {
      to: 'hera.ai.contact@gmail.com',
      from: 'information@eight8.tech', // SendGridで認証済みのメールアドレス
      replyTo: email, // ユーザーのメールアドレスに返信できるように設定
      subject: `[お問い合わせ] ${subject}`,
      text: `
お名前: ${name}
メールアドレス: ${email}
件名: ${subject}

お問い合わせ内容:
${message}

---
送信日時: ${new Date().toLocaleString('ja-JP')}
      `.trim(),
      html: `
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: linear-gradient(to right, #9333ea, #ec4899); color: white; padding: 20px; border-radius: 8px 8px 0 0; }
    .content { background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px; }
    .field { margin-bottom: 15px; }
    .label { font-weight: bold; color: #6b7280; }
    .value { margin-top: 5px; }
    .message-box { background: white; padding: 15px; border-radius: 6px; border-left: 4px solid #9333ea; }
    .footer { margin-top: 20px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h2 style="margin: 0;">💝 お問い合わせフォーム送信</h2>
    </div>
    <div class="content">
      <div class="field">
        <div class="label">お名前</div>
        <div class="value">${name}</div>
      </div>
      <div class="field">
        <div class="label">メールアドレス</div>
        <div class="value">${email}</div>
      </div>
      <div class="field">
        <div class="label">件名</div>
        <div class="value">${subject}</div>
      </div>
      <div class="field">
        <div class="label">お問い合わせ内容</div>
        <div class="message-box">${message.replace(/\n/g, '<br>')}</div>
      </div>
      <div class="footer">
        送信日時: ${new Date().toLocaleString('ja-JP')}<br>
        送信元: AIファミリー・シミュレーター お問い合わせフォーム
      </div>
    </div>
  </div>
</body>
</html>
      `.trim(),
    }

    await sgMail.send(msg)

    console.log('========== メール送信成功 ==========')
    console.log('送信日時:', new Date().toLocaleString('ja-JP'))
    console.log('送信先: hera.ai.contact@gmail.com')
    console.log('件名:', `[お問い合わせ] ${subject}`)
    console.log('=====================================')

    return NextResponse.json(
      {
        success: true,
        message: 'お問い合わせを受け付けました。ご連絡ありがとうございます。',
      },
      { status: 200 }
    )
  } catch (error: any) {
    console.error('お問い合わせフォームエラー:', error)

    // SendGridのエラーを詳細にログ
    if (error.response) {
      console.error('SendGridエラー詳細:', error.response.body)
    }

    return NextResponse.json(
      {
        error: 'メール送信中にエラーが発生しました。しばらく経ってから再度お試しください。',
        details: process.env.NODE_ENV === 'development' ? error.message : undefined
      },
      { status: 500 }
    )
  }
}
