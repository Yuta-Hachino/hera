'use client'

/**
 * 少子化対策への貢献・アプリの意義を説明するページ
 * 統計データと豪華なUIで訪問者を納得させる
 */
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useState, useEffect } from 'react'

export default function ImpactPage() {
  const router = useRouter()
  const [activeSection, setActiveSection] = useState(0)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    setIsVisible(true)
  }, [])

  // 統計データ
  const statistics = [
    {
      value: '1.26',
      label: '2022年の出生率',
      description: '過去最低を更新',
      trend: 'down',
      color: 'from-red-500 to-pink-500',
    },
    {
      value: '770,747',
      label: '2022年の出生数',
      description: '前年比-5.1%',
      trend: 'down',
      color: 'from-orange-500 to-red-500',
    },
    {
      value: '35.6%',
      label: '未婚率（30代前半）',
      description: '結婚への不安が要因',
      trend: 'up',
      color: 'from-yellow-500 to-orange-500',
    },
    {
      value: '67.2%',
      label: '子育て不安を感じる人',
      description: '経済的・心理的負担',
      trend: 'up',
      color: 'from-purple-500 to-pink-500',
    },
  ]

  // このアプリがもたらす効果
  const impacts = [
    {
      icon: '🎯',
      title: '心理的障壁の軽減',
      description:
        'AIによる疑似体験で「子どもを持つ未来」を具体的にイメージできるため、漠然とした不安が軽減されます。',
      percentage: '85%',
      detail: 'の利用者が出産・育児への不安が軽減したと回答（想定）',
    },
    {
      icon: '💡',
      title: 'ポジティブな動機付け',
      description:
        '未来の家族との対話や手紙を通じて、家族を持つことの喜びや幸せを感情的に体験できます。',
      percentage: '78%',
      detail: 'の利用者が結婚・出産に対して前向きになったと回答（想定）',
    },
    {
      icon: '🤝',
      title: 'カップル間の対話促進',
      description:
        'パートナーと一緒に体験することで、将来の家族像について自然に話し合うきっかけを提供します。',
      percentage: '92%',
      detail: 'のカップルが家族計画について話し合う機会が増えたと回答（想定）',
    },
    {
      icon: '📈',
      title: '社会全体への波及効果',
      description:
        '個人の意識変化が社会全体に波及し、少子化対策の一助となることが期待されます。',
      percentage: '2.5万人',
      detail: 'が利用すれば、年間約250人の出生数増加に寄与する可能性（想定）',
    },
  ]

  // ユーザーの声（想定）
  const testimonials = [
    {
      name: '田中 美咲さん（28歳）',
      role: '会社員',
      comment:
        '漠然と「子育ては大変そう」と思っていましたが、このアプリで未来の子どもと対話して、すごく幸せな気持ちになりました。前向きに考えられるようになりました。',
      rating: 5,
    },
    {
      name: '佐藤 健太さん・由美さん（32歳・30歳）',
      role: '夫婦',
      comment:
        '夫婦で一緒に体験しました。AIが描いた家族の未来を見て、二人で涙が出ました。子どもを持つ勇気をもらえました。',
      rating: 5,
    },
    {
      name: '鈴木 翔太さん（35歳）',
      role: 'エンジニア',
      comment:
        '経済的な不安が大きかったのですが、具体的な家族像を見ることで「なんとかなるかも」と思えるようになりました。技術的にも素晴らしいです。',
      rating: 5,
    },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      {/* ヘッダー */}
      <header className="bg-white shadow-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <Link
            href="/dashboard"
            className="flex items-center space-x-2 text-gray-700 hover:text-purple-600 transition"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
            <span className="font-medium">ダッシュボードに戻る</span>
          </Link>
        </div>
      </header>

      {/* ヒーローセクション */}
      <section className="relative overflow-hidden bg-gradient-to-r from-purple-600 via-pink-600 to-red-500 text-white py-24">
        <div className="absolute inset-0 bg-black opacity-10"></div>
        <div
          className={`relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center transition-all duration-1000 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
          }`}
        >
          <h1 className="text-5xl md:text-6xl font-extrabold mb-6 leading-tight">
            未来の家族を体験することで
            <br />
            <span className="text-yellow-300">少子化に立ち向かう</span>
          </h1>
          <p className="text-xl md:text-2xl mb-8 max-w-3xl mx-auto leading-relaxed">
            AIファミリー・シミュレーターは、テクノロジーの力で
            <br />
            「子どもを持つ未来」への不安を希望に変えます
          </p>
          <div className="flex justify-center gap-4">
            <button
              onClick={() => router.push('/start')}
              className="px-8 py-4 bg-white text-purple-600 font-bold rounded-full hover:bg-yellow-300 hover:text-purple-800 transition-all transform hover:scale-105 shadow-2xl"
            >
              今すぐ体験する
            </button>
            <button
              onClick={() => {
                const element = document.getElementById('statistics')
                element?.scrollIntoView({ behavior: 'smooth' })
              }}
              className="px-8 py-4 bg-transparent border-2 border-white text-white font-bold rounded-full hover:bg-white hover:text-purple-600 transition-all transform hover:scale-105"
            >
              詳しく知る
            </button>
          </div>
        </div>
        {/* 装飾要素 */}
        <div className="absolute top-10 left-10 w-32 h-32 bg-yellow-300 rounded-full opacity-20 animate-pulse"></div>
        <div className="absolute bottom-10 right-10 w-40 h-40 bg-pink-300 rounded-full opacity-20 animate-pulse"></div>
      </section>

      {/* 統計セクション */}
      <section id="statistics" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              日本の少子化 - 深刻な現実
            </h2>
            <p className="text-xl text-gray-600">
              統計データが示す、私たちが直面している課題
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {statistics.map((stat, index) => (
              <div
                key={index}
                className={`relative bg-gradient-to-br ${stat.color} p-8 rounded-2xl shadow-2xl transform hover:scale-105 transition-all duration-300 text-white`}
              >
                <div className="absolute top-0 right-0 p-4">
                  {stat.trend === 'down' ? (
                    <svg
                      className="w-8 h-8 text-white opacity-50"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={3}
                        d="M19 14l-7 7m0 0l-7-7m7 7V3"
                      />
                    </svg>
                  ) : (
                    <svg
                      className="w-8 h-8 text-white opacity-50"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={3}
                        d="M5 10l7-7m0 0l7 7m-7-7v18"
                      />
                    </svg>
                  )}
                </div>
                <div className="text-5xl font-extrabold mb-3">{stat.value}</div>
                <div className="text-lg font-semibold mb-2">{stat.label}</div>
                <div className="text-sm opacity-90">{stat.description}</div>
              </div>
            ))}
          </div>

          <div className="mt-12 text-center">
            <p className="text-gray-700 text-lg">
              出典: 厚生労働省「人口動態統計」、内閣府「少子化社会対策白書」
            </p>
          </div>
        </div>
      </section>

      {/* 不安の要因セクション */}
      <section className="py-20 bg-gradient-to-br from-gray-50 to-blue-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              なぜ、子どもを持つことに不安を感じるのか？
            </h2>
            <p className="text-xl text-gray-600">
              若年層が抱える主な懸念事項
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white p-8 rounded-xl shadow-lg">
              <div className="text-6xl mb-4">💰</div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">
                経済的不安
              </h3>
              <p className="text-gray-600 mb-4">
                教育費、生活費の増加、住宅費など、具体的な金額がイメージできず不安に。
              </p>
              <div className="bg-red-50 p-4 rounded-lg">
                <p className="text-red-700 font-semibold">
                  子育て費用: 約3,000万円/人
                </p>
              </div>
            </div>

            <div className="bg-white p-8 rounded-xl shadow-lg">
              <div className="text-6xl mb-4">😰</div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">
                心理的負担
              </h3>
              <p className="text-gray-600 mb-4">
                「自分にできるのか」「親としての責任」など、漠然とした不安が大きい。
              </p>
              <div className="bg-orange-50 p-4 rounded-lg">
                <p className="text-orange-700 font-semibold">
                  67.2%が子育てに不安
                </p>
              </div>
            </div>

            <div className="bg-white p-8 rounded-xl shadow-lg">
              <div className="text-6xl mb-4">🤷</div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">
                具体的イメージの欠如
              </h3>
              <p className="text-gray-600 mb-4">
                「子どもがいる生活」が想像できず、踏み出せない。
              </p>
              <div className="bg-yellow-50 p-4 rounded-lg">
                <p className="text-yellow-700 font-semibold">
                  イメージの欠如が意思決定を阻害
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ソリューションセクション */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              このアプリが提供する解決策
            </h2>
            <p className="text-xl text-gray-600">
              AIテクノロジーで不安を希望に変える
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
            {impacts.map((impact, index) => (
              <div
                key={index}
                className="bg-gradient-to-br from-purple-50 to-pink-50 p-10 rounded-2xl shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-2"
              >
                <div className="text-7xl mb-6">{impact.icon}</div>
                <h3 className="text-3xl font-bold text-gray-900 mb-4">
                  {impact.title}
                </h3>
                <p className="text-gray-700 mb-6 text-lg leading-relaxed">
                  {impact.description}
                </p>
                <div className="bg-white p-6 rounded-xl shadow-md">
                  <div className="text-4xl font-extrabold text-purple-600 mb-2">
                    {impact.percentage}
                  </div>
                  <p className="text-gray-600">{impact.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* テクノロジーセクション */}
      <section className="py-20 bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">
              最先端AIテクノロジーが実現する体験
            </h2>
            <p className="text-xl opacity-90">
              Google Gemini AIとADKエージェントシステムを活用
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white bg-opacity-10 backdrop-blur-lg p-8 rounded-xl">
              <div className="text-5xl mb-4">🤖</div>
              <h3 className="text-2xl font-bold mb-3">
                高度な対話AI
              </h3>
              <p className="opacity-90">
                自然な会話でユーザー情報を収集し、パーソナライズされた家族像を生成
              </p>
            </div>

            <div className="bg-white bg-opacity-10 backdrop-blur-lg p-8 rounded-xl">
              <div className="text-5xl mb-4">🎨</div>
              <h3 className="text-2xl font-bold mb-3">
                リアルな画像生成
              </h3>
              <p className="opacity-90">
                AIが生成する高品質な家族イラストで、視覚的に未来を体験
              </p>
            </div>

            <div className="bg-white bg-opacity-10 backdrop-blur-lg p-8 rounded-xl">
              <div className="text-5xl mb-4">✉️</div>
              <h3 className="text-2xl font-bold mb-3">
                感動的なストーリー
              </h3>
              <p className="opacity-90">
                未来の子どもからの手紙や家族の日常ストーリーで感情に訴える
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ユーザーの声セクション */}
      <section className="py-20 bg-gradient-to-br from-yellow-50 to-orange-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              体験者の声
            </h2>
            <p className="text-xl text-gray-600">
              実際に利用した方々の感想（想定）
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <div
                key={index}
                className="bg-white p-8 rounded-2xl shadow-xl relative"
              >
                <div className="absolute top-0 left-0 p-4">
                  <svg
                    className="w-12 h-12 text-purple-200"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z" />
                  </svg>
                </div>
                <div className="mb-4 pt-12">
                  <div className="flex text-yellow-400 mb-3">
                    {[...Array(testimonial.rating)].map((_, i) => (
                      <svg
                        key={i}
                        className="w-6 h-6"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    ))}
                  </div>
                </div>
                <p className="text-gray-700 mb-6 italic leading-relaxed">
                  「{testimonial.comment}」
                </p>
                <div className="border-t pt-4">
                  <p className="font-bold text-gray-900">{testimonial.name}</p>
                  <p className="text-gray-600 text-sm">{testimonial.role}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 社会への影響セクション */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              社会への波及効果
            </h2>
            <p className="text-xl text-gray-600">
              一人ひとりの意識変化が社会を変える
            </p>
          </div>

          <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-3xl p-12 text-white shadow-2xl">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
              <div>
                <div className="text-6xl font-extrabold mb-3">2.5万人</div>
                <p className="text-xl">が利用すれば</p>
              </div>
              <div className="flex items-center justify-center">
                <svg
                  className="w-16 h-16"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={3}
                    d="M13 7l5 5m0 0l-5 5m5-5H6"
                  />
                </svg>
              </div>
              <div>
                <div className="text-6xl font-extrabold mb-3">+250人</div>
                <p className="text-xl">の出生数増加に寄与</p>
              </div>
            </div>
            <div className="mt-8 text-center">
              <p className="text-lg opacity-90">
                ※ 利用者の1%が実際に出産に踏み切ると仮定（控えめな試算）
              </p>
            </div>
          </div>

          <div className="mt-16 grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-8 rounded-xl shadow-lg">
              <div className="text-5xl mb-4">🌱</div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">
                個人レベルの変化
              </h3>
              <ul className="space-y-3 text-gray-700">
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  結婚・出産への心理的障壁が低下
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  家族を持つことへのポジティブなイメージ形成
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">✓</span>
                  パートナーとの建設的な対話促進
                </li>
              </ul>
            </div>

            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-8 rounded-xl shadow-lg">
              <div className="text-5xl mb-4">🏙️</div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">
                社会レベルの変化
              </h3>
              <ul className="space-y-3 text-gray-700">
                <li className="flex items-start">
                  <span className="text-blue-600 mr-2">✓</span>
                  少子化トレンドの緩和に貢献
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-2">✓</span>
                  持続可能な社会保障制度の維持
                </li>
                <li className="flex items-start">
                  <span className="text-blue-600 mr-2">✓</span>
                  経済活力の向上と地域コミュニティの活性化
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTAセクション */}
      <section className="py-24 bg-gradient-to-r from-purple-600 via-pink-600 to-red-500 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-5xl font-extrabold mb-6">
            あなたも未来の家族を体験しませんか？
          </h2>
          <p className="text-2xl mb-10 opacity-90">
            一人ひとりの小さな一歩が、社会の大きな変化につながります
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => router.push('/start')}
              className="px-12 py-5 bg-white text-purple-600 font-bold text-xl rounded-full hover:bg-yellow-300 hover:text-purple-800 transition-all transform hover:scale-105 shadow-2xl"
            >
              今すぐ無料で体験する
            </button>
            <button
              onClick={() => router.push('/dashboard')}
              className="px-12 py-5 bg-transparent border-2 border-white text-white font-bold text-xl rounded-full hover:bg-white hover:text-purple-600 transition-all transform hover:scale-105"
            >
              ダッシュボードに戻る
            </button>
          </div>
          <p className="mt-8 text-sm opacity-75">
            ※ 本サービスは実験的なAIアプリケーションです。
          </p>
        </div>
      </section>

      {/* フッター */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h3 className="text-lg font-bold mb-4">AIファミリー・シミュレーター</h3>
              <p className="text-gray-400 text-sm">
                テクノロジーの力で、少子化問題に立ち向かう
              </p>
            </div>
            <div>
              <h3 className="text-lg font-bold mb-4">リンク</h3>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li>
                  <Link href="/terms" className="hover:text-white transition">
                    利用規約
                  </Link>
                </li>
                <li>
                  <Link href="/privacy" className="hover:text-white transition">
                    プライバシーポリシー
                  </Link>
                </li>
                <li>
                  <Link href="/dashboard" className="hover:text-white transition">
                    ダッシュボード
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-bold mb-4">お問い合わせ</h3>
              <p className="text-gray-400 text-sm">
                ご質問・ご意見は、ダッシュボードからお問い合わせください。
              </p>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400 text-sm">
            <p>&copy; 2024 AIファミリー・シミュレーター. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
