'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createSession } from '@/lib/api-client'
import Header from '@/components/Header'

export default function StartPage() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleStart = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const session = await createSession(true)  // 認証必要
      router.push(`/chat/${session.session_id}`)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'セッションの作成に失敗しました'
      )
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-100">
      <Header />

      <div className="flex items-center justify-center p-4 py-12">
        <div className="max-w-3xl w-full bg-white rounded-3xl shadow-2xl p-8 md:p-14">
          <div className="text-center">
            {/* アイコン */}
            <div className="mb-8">
              <div className="w-24 h-24 mx-auto bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center shadow-xl">
                <span className="text-5xl">💝</span>
              </div>
            </div>

            {/* タイトル */}
            <h1 className="text-4xl md:text-5xl font-extrabold text-gray-900 mb-4">
              AIファミリー・シミュレーター
            </h1>
            <p className="text-2xl text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600 font-bold mb-10">
              未来の家族を体験しよう
            </p>

            {/* 説明文 */}
            <div className="text-left space-y-6 mb-12">
              <p className="text-gray-700 text-lg leading-relaxed">
                このアプリケーションは、AI家族愛の神「ヘーラー（Hera）」との対話を通じて、
                あなたの未来の家族像を描き出します。
              </p>
              <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-6 border-2 border-purple-200 shadow-md">
                <h2 className="font-bold text-purple-900 mb-4 text-xl flex items-center">
                  <span className="mr-2 text-2xl">✨</span>
                  体験できること
                </h2>
                <ul className="space-y-3">
                  <li className="flex items-start">
                    <span className="text-purple-600 mr-3 text-xl font-bold">✓</span>
                    <span className="text-gray-700">AIエージェント「ヘーラー」との自然な対話</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-purple-600 mr-3 text-xl font-bold">✓</span>
                    <span className="text-gray-700">Live2Dアバターが話しかけてくる没入体験</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-purple-600 mr-3 text-xl font-bold">✓</span>
                    <span className="text-gray-700">あなたに合わせた家族の未来ストーリー生成</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-purple-600 mr-3 text-xl font-bold">✓</span>
                    <span className="text-gray-700">子どもを持つ未来をポジティブに体験</span>
                  </li>
                </ul>
              </div>
              <div className="bg-blue-50 rounded-xl p-4 border border-blue-200">
                <p className="text-sm text-blue-900 flex items-center justify-center">
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                  </svg>
                  所要時間：約10〜15分
                </p>
              </div>
            </div>

            {/* エラー表示 */}
            {error && (
              <div className="mb-6 p-4 bg-red-50 border-2 border-red-200 rounded-xl text-red-700">
                <p className="font-semibold">エラー</p>
                <p className="text-sm mt-1">{error}</p>
              </div>
            )}

            {/* 開始ボタン */}
            <button
              onClick={handleStart}
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-purple-600 via-pink-600 to-rose-600 text-white font-bold py-5 px-8 rounded-2xl text-xl hover:shadow-2xl focus:outline-none focus:ring-4 focus:ring-purple-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 disabled:hover:scale-100"
            >
              {isLoading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin h-6 w-6 mr-3" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>準備中...</span>
                </span>
              ) : (
                <span className="flex items-center justify-center">
                  <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                  体験を始める
                </span>
              )}
            </button>

            <p className="text-xs text-gray-500 mt-6">
              ※ このアプリケーションで収集した情報は、体験の提供のみに使用されます
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
