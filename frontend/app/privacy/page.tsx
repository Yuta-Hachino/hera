'use client'

import Header from '@/components/Header'
import Link from 'next/link'

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50">
      <Header />

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* ヘッダー */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">プライバシーポリシー</h1>
          <p className="text-gray-600">AI Family Simulator Privacy Policy</p>
          <div className="mt-6 inline-block bg-white px-6 py-3 rounded-full shadow-sm">
            <p className="text-sm text-gray-500">最終更新日: 2025年1月</p>
          </div>
        </div>

        {/* 本文 */}
        <div className="bg-white rounded-2xl shadow-xl p-8 md:p-12 space-y-8">
          {/* 第1条 */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4 pb-2 border-b-2 border-pink-200">
              第1条（個人情報）
            </h2>
            <p className="text-gray-700 leading-relaxed">
              「個人情報」とは、個人情報保護法にいう「個人情報」を指すものとし、生存する個人に関する情報であって、当該情報に含まれる氏名、生年月日、住所、電話番号、連絡先その他の記述等により特定の個人を識別できる情報及び容貌、指紋、声紋にかかるデータ、及び健康保険証の保険者番号などの当該情報単体から特定の個人を識別できる情報（個人識別情報）を指します。
            </p>
          </section>

          {/* 第2条 */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4 pb-2 border-b-2 border-pink-200">
              第2条（個人情報の収集方法）
            </h2>
            <div className="space-y-4 text-gray-700 leading-relaxed">
              <p>
                当社は、ユーザーが利用登録をする際に氏名、生年月日、住所、電話番号、メールアドレス、銀行口座番号、クレジットカード番号、運転免許証番号などの個人情報をお尋ねすることがあります。また、ユーザーと提携先などとの間でなされたユーザーの個人情報を含む取引記録や決済に関する情報を、当社の提携先（情報提供元、広告主、広告配信先などを含みます。以下、「提携先」といいます）などから収集することがあります。
              </p>
            </div>
          </section>

          {/* 第3条 */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4 pb-2 border-b-2 border-pink-200">
              第3条（個人情報を収集・利用する目的）
            </h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              当社が個人情報を収集・利用する目的は、以下のとおりです。
            </p>
            <ul className="list-disc list-inside space-y-2 text-gray-700 ml-4">
              <li>当社サービスの提供・運営のため</li>
              <li>ユーザーからのお問い合わせに回答するため（本人確認を行うことを含む）</li>
              <li>ユーザーが利用中のサービスの新機能、更新情報、キャンペーン等及び当社が提供する他のサービスの案内のメールを送付するため</li>
              <li>メンテナンス、重要なお知らせなど必要に応じたご連絡のため</li>
              <li>利用規約に違反したユーザーや、不正・不当な目的でサービスを利用しようとするユーザーの特定をし、ご利用をお断りするため</li>
              <li>ユーザーにご自身の登録情報の閲覧や変更、削除、ご利用状況の閲覧を行っていただくため</li>
              <li>有料サービスにおいて、ユーザーに利用料金を請求するため</li>
              <li>上記の利用目的に付随する目的</li>
            </ul>
          </section>

          {/* 第4条 */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4 pb-2 border-b-2 border-pink-200">
              第4条（利用目的の変更）
            </h2>
            <div className="space-y-4 text-gray-700 leading-relaxed">
              <p>
                当社は、利用目的が変更前と関連性を有すると合理的に認められる場合に限り、個人情報の利用目的を変更するものとします。
              </p>
              <p>
                利用目的の変更を行った場合には、変更後の目的について、当社所定の方法により、ユーザーに通知し、または本ウェブサイト上に公表するものとします。
              </p>
            </div>
          </section>

          {/* 第5条 */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4 pb-2 border-b-2 border-pink-200">
              第5条（個人情報の第三者提供）
            </h2>
            <div className="space-y-4 text-gray-700 leading-relaxed">
              <p>
                当社は、次に掲げる場合を除いて、あらかじめユーザーの同意を得ることなく、第三者に個人情報を提供することはありません。ただし、個人情報保護法その他の法令で認められる場合を除きます。
              </p>
              <ul className="list-disc list-inside space-y-2 text-gray-700 ml-4">
                <li>人の生命、身体または財産の保護のために必要がある場合であって、本人の同意を得ることが困難であるとき</li>
                <li>公衆衛生の向上または児童の健全な育成の推進のために特に必要がある場合であって、本人の同意を得ることが困難であるとき</li>
                <li>国の機関もしくは地方公共団体またはその委託を受けた者が法令の定める事務を遂行することに対して協力する必要がある場合であって、本人の同意を得ることにより当該事務の遂行に支障を及ぼすおそれがあるとき</li>
                <li>予め次の事項を告知あるいは公表し、かつ当社が個人情報保護委員会に届出をしたとき</li>
              </ul>
            </div>
          </section>

          {/* 第6条 */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4 pb-2 border-b-2 border-pink-200">
              第6条（個人情報の開示）
            </h2>
            <div className="space-y-4 text-gray-700 leading-relaxed">
              <p>
                当社は、本人から個人情報の開示を求められたときは、本人に対し、遅滞なくこれを開示します。ただし、開示することにより次のいずれかに該当する場合は、その全部または一部を開示しないこともあり、開示しない決定をした場合には、その旨を遅滞なく通知します。
              </p>
              <ul className="list-disc list-inside space-y-2 text-gray-700 ml-4">
                <li>本人または第三者の生命、身体、財産その他の権利利益を害するおそれがある場合</li>
                <li>当社の業務の適正な実施に著しい支障を及ぼすおそれがある場合</li>
                <li>その他法令に違反することとなる場合</li>
              </ul>
            </div>
          </section>

          {/* 第7条 */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4 pb-2 border-b-2 border-pink-200">
              第7条（個人情報の訂正および削除）
            </h2>
            <div className="space-y-4 text-gray-700 leading-relaxed">
              <p>
                ユーザーは、当社の保有する自己の個人情報が誤った情報である場合には、当社が定める手続きにより、当社に対して個人情報の訂正、追加または削除（以下「訂正等」といいます）を請求することができます。
              </p>
              <p>
                当社は、ユーザーから前項の請求を受けてその請求に応じる必要があると判断した場合には、遅滞なく、当該個人情報の訂正等を行うものとします。
              </p>
            </div>
          </section>

          {/* 第8条 */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4 pb-2 border-b-2 border-pink-200">
              第8条（プライバシーポリシーの変更）
            </h2>
            <div className="space-y-4 text-gray-700 leading-relaxed">
              <p>
                本ポリシーの内容は、法令その他本ポリシーに別段の定めのある事項を除いて、ユーザーに通知することなく、変更することができるものとします。
              </p>
              <p>
                当社が別途定める場合を除いて、変更後のプライバシーポリシーは、本ウェブサイトに掲載したときから効力を生じるものとします。
              </p>
            </div>
          </section>

          {/* お問い合わせ先 */}
          <section className="bg-gradient-to-r from-purple-50 to-pink-50 p-6 rounded-xl">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">お問い合わせ先</h2>
            <p className="text-gray-700 leading-relaxed">
              本ポリシーに関するお問い合わせは、下記の窓口までお願いいたします。
            </p>
            <div className="mt-4">
              <Link href="/contact" className="inline-flex items-center space-x-2 text-purple-600 hover:text-purple-800 font-medium transition">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <span>お問い合わせフォームはこちら</span>
              </Link>
            </div>
          </section>

          {/* フッター */}
          <div className="pt-8 mt-8 border-t border-gray-200">
            <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
              <Link href="/terms" className="text-purple-600 hover:text-purple-800 font-medium transition">
                利用規約 →
              </Link>
              <Link href="/dashboard" className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-3 rounded-lg hover:shadow-lg transition">
                ダッシュボードに戻る
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
