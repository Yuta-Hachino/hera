'use client'

import { useAuth } from '@/lib/auth-context-firebase'
import { signOut } from '@/lib/firebase-auth'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

export default function Header() {
  const { user, loading } = useAuth()
  const router = useRouter()

  const handleLogout = async () => {
    try {
      await signOut()
      router.push('/')
    } catch (error) {
      console.error('ログアウトエラー:', error)
    }
  }

  if (loading || !user) {
    return null
  }

  return (
    <header className="bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* ロゴ */}
          <Link href="/start" className="flex items-center space-x-2 hover:opacity-80 transition">
            <span className="text-2xl">💝</span>
            <span className="font-bold text-xl">AI Family Simulator</span>
          </Link>

          {/* ナビゲーション */}
          <nav className="flex items-center space-x-6">
            <Link
              href="/dashboard"
              className="hover:text-pink-200 transition font-medium"
            >
              ダッシュボード
            </Link>

            <Link
              href="/contact"
              className="flex items-center space-x-2 hover:text-pink-200 transition font-medium"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
              <span>お問い合わせ</span>
            </Link>

            <Link
              href="/profile"
              className="flex items-center space-x-2 hover:text-pink-200 transition font-medium"
            >
              <span>👤</span>
              <span>マイページ</span>
            </Link>

            <button
              onClick={handleLogout}
              className="bg-white text-purple-600 px-4 py-2 rounded-lg hover:bg-pink-50 transition font-medium shadow-md"
            >
              ログアウト
            </button>
          </nav>
        </div>
      </div>
    </header>
  )
}
