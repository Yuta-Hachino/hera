'use client'

import Header from '@/components/Header'
import Link from 'next/link'

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50">
      <Header />

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* ヘッダー */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">利用規約</h1>
          <p className="text-gray-600">AI Family Simulator Terms of Service</p>
          <div className="mt-6 inline-block bg-white px-6 py-3 rounded-full shadow-sm">
            <p className="text-sm text-gray-500">最終更新日: 2025年1月</p>
          </div>
        </div>

        {/* 本文 */}
        <div className="bg-white rounded-2xl shadow-xl p-8 md:p-12 space-y-8">
          {/* 第1条 */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4 pb-2 border-b-2 border-purple-200">
              第1条（適用範囲）
            </h2>
            <p className="text-gray-700 leading-relaxed">
              本利用規約（以下「本規約」といいます）は、AI Family Simulator（以下「本サービス」といいます）の提供条件及び本サービスの利用に関する当社と登録ユーザーとの間の権利義務関係を定めることを目的とし、ユーザーと当社との間の本サービスの利用に関わる一切の関係に適用されます。
            </p>
          </section>

          {/* 第2条 */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4 pb-2 border-b-2 border-purple-200">
              第2条（定義）
            </h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              本規約において使用する以下の用語は、各々以下に定める意味を有するものとします。
            </p>
            <ul className="list-disc list-inside space-y-2 text-gray-700 ml-4">
              <li>「サービス利用契約」とは、本規約を契約条件として当社とユーザーの間で締結される、本サービスの利用契約を意味します。</li>
              <li>「知的財産権」とは、著作権、特許権、実用新案権、意匠権、商標権その他の知的財産権（それらの権利を取得し、またはそれらの権利につき登録等を出願する権利を含みます）を意味します。</li>
              <li>「投稿データ」とは、ユーザーが本サービスを利用して投稿その他送信するコンテンツ（文章、画像、動画その他のデータを含みますがこれらに限りません）を意味します。</li>
              <li>「当社」とは、本サービスを運営する事業者を意味します。</li>
              <li>「ユーザー」とは、本サービスを利用する全ての方を意味します。</li>
            </ul>
          </section>

          {/* 第3条 */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4 pb-2 border-b-2 border-purple-200">
              第3条（本規約への同意）
            </h2>
            <div className="space-y-4 text-gray-700 leading-relaxed">
              <p>
                ユーザーは、本規約の定めに従って本サービスを利用しなければなりません。ユーザーは、本規約に有効かつ取消不能な同意をしないい限り本サービスを利用できません。
              </p>
              <p>
                本サービスを実際に利用することによって、ユーザーは、本規約に有効かつ取消不能な同意をしたものとみなされます。
              </p>
            </div>
          </section>

          {/* 第4条 */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4 pb-2 border-b-2 border-purple-200">
              第4条（利用登録）
            </h2>
            <div className="space-y-4 text-gray-700 leading-relaxed">
              <p>
                本サービスの利用を希望する方（以下「登録希望者」といいます）は、本規約を遵守することに同意し、かつ当社の定める一定の情報（以下「登録情報」といいます）を当社の定める方法で当社に提供することにより、当社に対し、本サービスの利用の登録を申請することができます。
              </p>
              <p>
                当社は、当社の基準に従って、登録希望者の登録の可否を判断し、当社が登録を認める場合にはその旨を登録希望者に通知します。登録希望者のユーザーとしての登録は、当社が本項の通知を行ったことをもって完了したものとします。
              </p>
            </div>
          </section>

          {/* 第5条 */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4 pb-2 border-b-2 border-purple-200">
              第5条（禁止事項）
            </h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              ユーザーは、本サービスの利用にあたり、以下の各号のいずれかに該当する行為または該当すると当社が判断する行為をしてはなりません。
            </p>
            <ul className="list-disc list-inside space-y-2 text-gray-700 ml-4">
              <li>法令に違反する行為または犯罪行為に関連する行為</li>
              <li>当社、本サービスの他の利用者またはその他の第三者に対する詐欺または脅迫行為</li>
              <li>公序良俗に反する行為</li>
              <li>当社、本サービスの他の利用者またはその他の第三者の知的財産権、肖像権、プライバシーの権利、名誉、その他の権利または利益を侵害する行為</li>
              <li>本サービスを通じ、以下に該当し、または該当すると当社が判断する情報を当社または本サービスの他の利用者に送信すること</li>
              <li>過度に暴力的または残虐な表現を含む情報</li>
              <li>コンピューター・ウィルスその他の有害なコンピューター・プログラムを含む情報</li>
              <li>当社、本サービスの他の利用者またはその他の第三者の名誉または信用を毀損する表現を含む情報</li>
              <li>本サービスのネットワークまたはシステム等に過度な負荷をかける行為</li>
              <li>当社が提供するソフトウェアその他のシステムに対するリバースエンジニアリングその他の解析行為</li>
              <li>本サービスの運営を妨害するおそれのある行為</li>
              <li>当社のネットワークまたはシステム等への不正アクセス</li>
              <li>第三者に成りすます行為</li>
              <li>本サービスの他の利用者のIDまたはパスワードを利用する行為</li>
              <li>その他、当社が不適切と判断する行為</li>
            </ul>
          </section>

          {/* 第6条 */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4 pb-2 border-b-2 border-purple-200">
              第6条（免責事項）
            </h2>
            <div className="space-y-4 text-gray-700 leading-relaxed">
              <p>
                当社は、本サービスに事実上または法律上の瑕疵（安全性、信頼性、正確性、完全性、有効性、特定の目的への適合性、セキュリティなどに関する欠陥、エラーやバグ、権利侵害などを含みます）がないことを明示的にも黙示的にも保証しておりません。
              </p>
              <p>
                当社は、本サービスに起因してユーザーに生じたあらゆる損害について一切の責任を負いません。ただし、本サービスに関する当社とユーザーとの間の契約（本規約を含みます）が消費者契約法に定める消費者契約となる場合、この免責規定は適用されません。
              </p>
            </div>
          </section>

          {/* 第7条 */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-4 pb-2 border-b-2 border-purple-200">
              第7条（本規約の変更）
            </h2>
            <p className="text-gray-700 leading-relaxed">
              当社は、当社が必要と認めた場合は、本規約を変更できるものとします。本規約を変更する場合、変更後の本規約の施行時期および内容を当社ウェブサイト上での掲示その他の適切な方法により周知し、またはユーザーに通知します。
            </p>
          </section>

          {/* フッター */}
          <div className="pt-8 mt-8 border-t border-gray-200">
            <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
              <Link href="/privacy" className="text-purple-600 hover:text-purple-800 font-medium transition">
                プライバシーポリシー →
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
