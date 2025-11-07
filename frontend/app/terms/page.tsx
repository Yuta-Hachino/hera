'use client'

import Link from 'next/link'

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8 md:p-12">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">利用規約</h1>

          <div className="space-y-6 text-gray-700">
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">第1条（適用）</h2>
              <p>
                本規約は、AIファミリー・シミュレーター（以下「本サービス」といいます）の利用に関する条件を定めるものです。
                本サービスを利用される方は、本規約に同意したものとみなされます。
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">第2条（サービスの内容）</h2>
              <p>
                本サービスは、AIを活用した家族シミュレーション体験を提供するものです。
                本サービスで生成されるコンテンツは、すべてAIによる仮想的なものであり、
                実在の人物、団体、出来事とは一切関係ありません。
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">第3条（免責事項）</h2>
              <div className="space-y-3">
                <p>
                  本サービスの提供者は、本サービスの利用により発生したいかなる損害、トラブル、
                  不利益についても一切の責任を負いません。
                </p>
                <p>
                  本サービスで提供される情報、コンテンツの正確性、完全性、有用性について、
                  いかなる保証も行いません。
                </p>
                <p>
                  本サービスの利用により生じた精神的苦痛、感情的な影響、その他いかなる損害についても、
                  提供者は一切の責任を負いません。
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">第4条（サービスの中断・終了）</h2>
              <p>
                提供者は、事前の通知なく本サービスの全部または一部を変更、中断、終了することができます。
                これにより利用者に生じた損害について、提供者は一切の責任を負いません。
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">第5条（AIの特性に関する注意事項）</h2>
              <div className="space-y-3">
                <p>
                  本サービスで使用されるAIは、予期しない出力や不適切な内容を生成する可能性があります。
                </p>
                <p>
                  AIが生成したコンテンツに関して、利用者が不快感や精神的苦痛を感じた場合でも、
                  提供者は一切の責任を負いません。
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">第6条（利用者の責任）</h2>
              <p>
                利用者は、本サービスの利用にあたり、自己の責任において行うものとし、
                本サービスの利用により第三者に損害を与えた場合、自己の責任と費用において解決するものとします。
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">第7条（規約の変更）</h2>
              <p>
                提供者は、利用者の承諾を得ることなく、本規約を変更することができます。
                変更後の規約は、本サービス上に掲載された時点で効力を生じるものとします。
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">第8条（準拠法・管轄裁判所）</h2>
              <p>
                本規約の解釈にあたっては、日本法を準拠法とします。
                本サービスに関して紛争が生じた場合には、東京地方裁判所を第一審の専属的合意管轄裁判所とします。
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
