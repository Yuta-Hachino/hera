'use client'

/**
 * ダッシュボードページ
 * ユーザーのセッション一覧と新規セッション作成
 */
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { withAuth } from '@/lib/with-auth'
import { useAuth } from '@/lib/auth-context'
import { createSession } from '@/lib/api-client'

function DashboardPage() {
  const router = useRouter()
  const { user, signOut } = useAuth()
  const [isCreatingSession, setIsCreatingSession] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCreateSession = async () => {
    try {
      setIsCreatingSession(true)
      setError(null)

      // セッション作成（認証必要）
      const response = await createSession(true)
      const sessionId = response.session_id

      // チャットページに遷移
      router.push(`/chat/${sessionId}`)
    } catch (err) {
      console.error('Session creation error:', err)
      setError('セッションの作成に失敗しました。もう一度お試しください。')
      setIsCreatingSession(false)
    }
  }

  const handleSignOut = async () => {
    try {
      await signOut()
      router.push('/login')
    } catch (err) {
      console.error('Sign out error:', err)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* ヘッダー */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">
            AIファミリー・シミュレーター
          </h1>
          <div className="flex items-center gap-4">
            <div className="text-sm text-gray-600">
              {user?.email}
            </div>
            <button
              onClick={handleSignOut}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              ログアウト
            </button>
          </div>
        </div>
      </header>

      {/* メインコンテンツ */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            未来の家族を体験しましょう
          </h2>
          <p className="text-lg text-gray-600">
            AIがあなたの理想の家族像を作り上げます
          </p>
        </div>

        {error && (
          <div className="max-w-md mx-auto mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <div className="max-w-md mx-auto">
          <button
            onClick={handleCreateSession}
            disabled={isCreatingSession}
            className="w-full flex items-center justify-center gap-3 px-6 py-4 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-lg"
          >
            {isCreatingSession ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>セッション作成中...</span>
              </>
            ) : (
              <>
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
                    d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                  />
                </svg>
                <span>新しいセッションを開始</span>
              </>
            )}
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
