'use client'

/**
 * ダッシュボードページ
 * ユーザーのセッション一覧と新規セッション作成
 */
import { useRouter } from 'next/navigation'
import { withAuth } from '@/lib/with-auth'
import Link from 'next/link'
import { useState } from 'react'

function DashboardPage() {
  const router = useRouter()
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)

  const handleStartExperience = () => {
    // start画面に遷移
    router.push('/start')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 flex">
      {/* サイドバー */}
      <aside
        className={`${
          isSidebarOpen ? 'w-64' : 'w-0'
        } bg-white shadow-xl transition-all duration-300 overflow-hidden flex flex-col`}
      >
        <div className="p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-6">メニュー</h2>

          <nav className="space-y-2">
            {/* Startページへのリンク */}
            <Link
              href="/start"
              className="flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-purple-50 transition group"
            >
              <svg
                className="w-5 h-5 text-purple-600 group-hover:text-purple-700"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M14 5l7 7m0 0l-7 7m7-7H3"
                />
              </svg>
              <span className="text-gray-700 font-medium group-hover:text-purple-700">
                体験を始める
              </span>
            </Link>

            {/* 少子化対策への貢献ページへのリンク */}
            <Link
              href="/impact"
              className="flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-gradient-to-r hover:from-pink-50 hover:to-purple-50 transition group border-2 border-transparent hover:border-pink-200"
            >
              <svg
                className="w-5 h-5 text-pink-600 group-hover:text-pink-700"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                />
              </svg>
              <span className="text-pink-700 font-bold group-hover:text-pink-800">
                このアプリの意義
              </span>
            </Link>

            {/* 規約ページへのリンク */}
            <Link
              href="/terms"
              className="flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-gray-50 transition group"
            >
              <svg
                className="w-5 h-5 text-gray-600 group-hover:text-gray-700"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <span className="text-gray-700 font-medium group-hover:text-gray-800">
                利用規約
              </span>
            </Link>

            {/* プライバシーポリシーへのリンク */}
            <Link
              href="/privacy"
              className="flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-gray-50 transition group"
            >
              <svg
                className="w-5 h-5 text-gray-600 group-hover:text-gray-700"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                />
              </svg>
              <span className="text-gray-700 font-medium group-hover:text-gray-800">
                プライバシーポリシー
              </span>
            </Link>
          </nav>
        </div>

        {/* サイドバー下部の注意書き */}
        <div className="mt-auto p-6 border-t border-gray-200">
          <div className="text-xs text-gray-500 space-y-2">
            <p className="font-semibold text-gray-700">⚠️ 重要なお知らせ</p>
            <p>
              本サービスは実験的なAIアプリケーションです。
              発生したトラブルや損害について、運営者は一切の責任を負いません。
            </p>
          </div>
        </div>
      </aside>

      {/* サイドバー切り替えボタン */}
      <button
        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
        className="fixed left-0 top-20 bg-white shadow-lg rounded-r-lg p-2 z-50 hover:bg-gray-50 transition"
      >
        <svg
          className={`w-6 h-6 text-gray-600 transform transition-transform ${
            isSidebarOpen ? '' : 'rotate-180'
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 19l-7-7 7-7"
          />
        </svg>
      </button>

      {/* メインコンテンツ */}
      <main className="flex-1 px-4 sm:px-6 lg:px-8 py-12 overflow-auto">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            未来の家族を体験しましょう
          </h2>
          <p className="text-xl text-gray-600">
            AIがあなたの理想の家族像を作り上げます
          </p>
        </div>

        <div className="max-w-2xl mx-auto space-y-4">
          <button
            onClick={handleStartExperience}
            className="w-full flex items-center justify-center gap-3 px-6 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-medium rounded-lg hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 transition-all transform hover:scale-105 shadow-lg"
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
                d="M14 5l7 7m0 0l-7 7m7-7H3"
              />
            </svg>
            <span>体験を始める</span>
          </button>

          {/* このアプリの意義へのボタン */}
          <button
            onClick={() => router.push('/impact')}
            className="w-full flex items-center justify-center gap-3 px-6 py-4 bg-gradient-to-r from-pink-500 via-red-500 to-orange-500 text-white font-medium rounded-lg hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-pink-500 transition-all transform hover:scale-105 shadow-lg border-2 border-yellow-300"
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
                d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
              />
            </svg>
            <span className="font-bold">このアプリの意義を知る - 少子化対策への貢献</span>
          </button>
        </div>

        {/* 説明セクション */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-indigo-600 mb-4">
              <svg
                className="w-12 h-12 mx-auto"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2 text-center">
              対話形式のヒアリング
            </h3>
            <p className="text-gray-600 text-center">
              AIがあなたの理想の家族像について優しく質問します
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-indigo-600 mb-4">
              <svg
                className="w-12 h-12 mx-auto"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2 text-center">
              家族との会話
            </h3>
            <p className="text-gray-600 text-center">
              AIで生成された未来の家族と実際に対話できます
            </p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="text-indigo-600 mb-4">
              <svg
                className="w-12 h-12 mx-auto"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2 text-center">
              旅行計画の作成
            </h3>
            <p className="text-gray-600 text-center">
              家族との対話から未来の旅行プランを作成します
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}

export default withAuth(DashboardPage)
