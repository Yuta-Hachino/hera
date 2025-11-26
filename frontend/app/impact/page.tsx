'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Header from '@/components/Header'

export default function ImpactPage() {
  const router = useRouter()
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    setIsVisible(true)
  }, [])

  const statistics = [
    {
      value: '1.26',
      label: '2022年の出生率',
      description: '過去最低を更新',
      color: 'from-red-500 to-pink-500',
    },
    {
      value: '770,747',
      label: '2022年の出生数',
      description: '前年比-5.1%',
      color: 'from-orange-500 to-red-500',
    },
    {
      value: '35.6%',
      label: '未婚率（30代前半）',
      description: '結婚への不安が要因',
      color: 'from-yellow-500 to-orange-500',
    },
    {
      value: '67.2%',
      label: '子育て不安を感じる人',
      description: '経済的・心理的負担',
      color: 'from-purple-500 to-pink-500',
    },
  ]

  const impacts = [
    {
      icon: '🎯',
      title: '心理的障壁の軽減',
      description:
        'AIによる疑似体験で「子どもを持つ未来」を具体的にイメージできるため、漠然とした不安が軽減されます。',
    },
    {
      icon: '💡',
      title: 'ポジティブな動機付け',
      description:
        '未来の家族との対話や手紙を通じて、家族を持つことの喜びや幸せを感情的に体験できます。',
    },
    {
      icon: '🤝',
      title: 'カップル間の対話促進',
      description:
        'パートナーと一緒に体験することで、将来の家族像について自然に話し合うきっかけを提供します。',
    },
    {
      icon: '📈',
      title: '社会全体への波及効果',
      description:
        '個人の意識変化が社会全体に波及し、少子化対策の一助となることが期待されます。',
    },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      <Header />

      {/* ヒーローセクション */}
      <section className="relative overflow-hidden bg-gradient-to-r from-purple-600 via-pink-600 to-rose-500 text-white py-20">
        <div className="absolute inset-0 bg-black opacity-10"></div>
        <div className="absolute top-0 right-0 w-96 h-96 bg-white/10 rounded-full -mr-48 -mt-48"></div>
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-white/10 rounded-full -ml-32 -mb-32"></div>

        <div
          className={`relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center transition-all duration-1000 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
          }`}
        >
          <h1 className="text-5xl md:text-6xl font-extrabold mb-6 leading-tight drop-shadow-2xl">
            未来の家族を体験することで
            <br />
            少子化問題に向き合う
          </h1>
          <p className="text-xl md:text-2xl mb-10 text-pink-100 drop-shadow-lg">
            AIテクノロジーが描く、新しい家族の形
          </p>
        </div>
      </section>

      {/* 統計データセクション */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">日本の少子化の現状</h2>
            <p className="text-gray-600 text-lg">深刻化する少子化問題に、私たちができること</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {statistics.map((stat, index) => (
              <div
                key={index}
                className="bg-gradient-to-br from-white to-gray-50 rounded-2xl p-6 shadow-xl hover:shadow-2xl transition transform hover:-translate-y-2"
              >
                <div className={`text-5xl font-extrabold bg-gradient-to-r ${stat.color} bg-clip-text text-transparent mb-2`}>
                  {stat.value}
                </div>
                <div className="text-lg font-bold text-gray-800 mb-1">{stat.label}</div>
                <div className="text-sm text-gray-600">{stat.description}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 効果セクション */}
      <section className="py-16 bg-gradient-to-br from-purple-50 to-pink-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">このアプリがもたらす効果</h2>
            <p className="text-gray-600 text-lg">テクノロジーの力で、未来への不安を希望に変える</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {impacts.map((impact, index) => (
              <div
                key={index}
                className="bg-white rounded-2xl p-8 shadow-xl hover:shadow-2xl transition"
              >
                <div className="flex items-start space-x-4">
                  <div className="text-5xl flex-shrink-0">{impact.icon}</div>
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-3">{impact.title}</h3>
                    <p className="text-gray-700 leading-relaxed">{impact.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ミッションセクション */}
      <section className="py-16 bg-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-3xl p-12 text-white shadow-2xl">
            <h2 className="text-4xl font-bold mb-6">私たちのミッション</h2>
            <p className="text-xl leading-relaxed mb-8">
              AIテクノロジーを活用し、一人ひとりが「家族を持つ未来」を前向きに描ける社会を実現する。
              それが、持続可能な社会への第一歩です。
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/start"
                className="bg-white text-purple-600 px-8 py-4 rounded-xl font-bold text-lg hover:bg-gray-100 transition shadow-lg transform hover:scale-105"
              >
                今すぐ体験する
              </Link>
              <Link
                href="/dashboard"
                className="bg-purple-700 text-white px-8 py-4 rounded-xl font-bold text-lg hover:bg-purple-800 transition shadow-lg transform hover:scale-105"
              >
                ダッシュボードへ
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* フッター */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h3 className="text-xl font-bold mb-4">AI Family Simulator</h3>
              <p className="text-gray-400">未来の家族を体験し、前向きな一歩を踏み出そう</p>
            </div>
            <div>
              <h3 className="text-xl font-bold mb-4">リンク</h3>
              <ul className="space-y-2">
                <li><Link href="/dashboard" className="text-gray-400 hover:text-white transition">ダッシュボード</Link></li>
                <li><Link href="/profile" className="text-gray-400 hover:text-white transition">マイページ</Link></li>
                <li><Link href="/contact" className="text-gray-400 hover:text-white transition">お問い合わせ</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="text-xl font-bold mb-4">法的情報</h3>
              <ul className="space-y-2">
                <li><Link href="/terms" className="text-gray-400 hover:text-white transition">利用規約</Link></li>
                <li><Link href="/privacy" className="text-gray-400 hover:text-white transition">プライバシーポリシー</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2025 AI Family Simulator. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
