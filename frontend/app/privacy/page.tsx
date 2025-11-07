'use client'

import Link from 'next/link'

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8 md:p-12">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">プライバシーポリシー</h1>

          <div className="space-y-6 text-gray-700">
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">1. 個人情報の取得</h2>
              <p>
                本サービスでは、Google認証を通じて以下の情報を取得します：
              </p>
              <ul className="list-disc list-inside mt-2 space-y-1 ml-4">
                <li>氏名</li>
                <li>メールアドレス</li>
                <li>プロフィール画像</li>
                <li>Google アカウントID</li>
              </ul>
              <p className="mt-2">
                また、サービス利用時に以下の情報を収集する場合があります：
              </p>
              <ul className="list-disc list-inside mt-2 space-y-1 ml-4">
                <li>年齢</li>
                <li>居住地</li>
                <li>性格特性に関する情報</li>
                <li>サービス利用履歴</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">2. 個人情報の利用目的</h2>
              <p>
                取得した個人情報は、以下の目的で利用します：
              </p>
              <ul className="list-disc list-inside mt-2 space-y-1 ml-4">
                <li>本サービスの提供・運営</li>
                <li>ユーザー認証</li>
                <li>AIによる家族シミュレーション体験のパーソナライズ</li>
                <li>サービスの改善・開発</li>
                <li>お問い合わせへの対応</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">3. 個人情報の管理</h2>
              <p>
                当サービスは、個人情報の漏洩、滅失、毀損を防止するため、
                適切な安全管理措置を講じます。ただし、完全な安全性を保証するものではありません。
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">4. 個人情報の第三者提供</h2>
              <div className="space-y-3">
                <p>
                  当サービスは、以下の場合を除き、個人情報を第三者に提供しません：
                </p>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>ユーザーの同意がある場合</li>
                  <li>法令に基づく場合</li>
                  <li>人の生命、身体または財産の保護のために必要がある場合</li>
                </ul>
                <p className="mt-3">
                  本サービスは、Google Firebase、Google Cloud Platform等のサードパーティサービスを利用しており、
                  これらのサービスにおいて個人情報が処理される場合があります。
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">5. Cookieの使用</h2>
              <p>
                本サービスでは、ユーザーの利便性向上のためCookieを使用します。
                Cookieの使用を希望されない場合は、ブラウザの設定で無効にすることができますが、
                サービスの一部機能が正常に動作しない場合があります。
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">6. AIによるデータ処理</h2>
              <div className="space-y-3">
                <p>
                  本サービスでは、Google Gemini等のAIサービスを使用しています。
                </p>
                <p>
                  ユーザーが入力した情報は、これらのAIサービスで処理される場合があります。
                  AIサービスにおけるデータの取り扱いについては、各サービスのプライバシーポリシーをご確認ください。
                </p>
                <p className="font-semibold text-gray-900">
                  重要：AIサービスで処理されたデータの完全な削除や、処理内容の追跡を保証することはできません。
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">7. 免責事項</h2>
              <div className="space-y-3">
                <p>
                  本サービスの提供者は、個人情報の取り扱いについて最善の努力を行いますが、
                  以下の事項について一切の責任を負いません：
                </p>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>第三者によるサービスへの不正アクセスによる情報漏洩</li>
                  <li>ユーザーの過失による情報の漏洩</li>
                  <li>AIサービスにおける予期しないデータ処理</li>
                  <li>サードパーティサービスにおける個人情報の取り扱い</li>
                </ul>
              </div>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">8. プライバシーポリシーの変更</h2>
              <p>
                当サービスは、ユーザーへの事前の通知なく、本プライバシーポリシーを変更することがあります。
                変更後のプライバシーポリシーは、本サービス上に掲載された時点で効力を生じるものとします。
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">9. お問い合わせ</h2>
              <p>
                本プライバシーポリシーに関するお問い合わせは、本サービスのお問い合わせフォームよりご連絡ください。
                ただし、回答を保証するものではありません。
              </p>
            </section>
          </div>

          <div className="mt-10 pt-6 border-t border-gray-200">
            <p className="text-sm text-gray-500 mb-6">最終更新日: 2025年1月7日</p>
            <Link
              href="/dashboard"
              className="inline-block bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-3 rounded-lg hover:shadow-lg transition font-semibold"
            >
              ダッシュボードに戻る
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
