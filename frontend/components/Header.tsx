'use client'

import { useAuth } from '@/lib/auth-context'
import { signOut } from '@/lib/firebase'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useState } from 'react'

export default function Header() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const handleLogout = async () => {
    try {
      await signOut()
      router.push('/')
    } catch (error) {
      console.error('ログアウトエラー:', error)
    }
  }

  return (
    <header className="bg-gradient-to-r from-purple-600 via-pink-500 to-rose-500 text-white shadow-xl sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* ロゴ */}
          <Link href={user ? "/dashboard" : "/"} className="flex items-center space-x-3 hover:opacity-90 transition group">
            <div className="relative">
              <span className="text-3xl transform group-hover:scale-110 transition-transform inline-block">💝</span>
              <div className="absolute -inset-1 bg-white/20 rounded-full blur opacity-0 group-hover:opacity-100 transition"></div>
            </div>
            <span className="font-bold text-xl tracking-tight hidden sm:inline-block">
              AI Family Simulator
            </span>
            <span className="font-bold text-xl tracking-tight sm:hidden">
              AFS
            </span>
          </Link>

          {/* デスクトップナビゲーション */}
          <nav className="hidden md:flex items-center space-x-1">
            {user ? (
              <>
                <Link
                  href="/dashboard"
                  className="px-4 py-2 rounded-lg hover:bg-white/10 transition font-medium flex items-center space-x-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                  </svg>
                  <span>ダッシュボード</span>
                </Link>

                <Link
                  href="/chat"
                  className="px-4 py-2 rounded-lg hover:bg-white/10 transition font-medium flex items-center space-x-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                  <span>チャット</span>
                </Link>

                {/* ユーザーアイコン */}
                <Link
                  href="/profile"
                  className="ml-2 p-2 rounded-full hover:bg-white/10 transition flex items-center justify-center"
                  title="プロフィール"
                >
                  <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                    {user.photoURL ? (
                      <img
                        src={user.photoURL}
                        alt="Profile"
                        className="w-full h-full rounded-full object-cover"
                      />
                    ) : (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    )}
                  </div>
                </Link>

                <button
                  onClick={handleLogout}
                  className="ml-2 bg-white/20 hover:bg-white/30 backdrop-blur-sm px-5 py-2 rounded-lg transition font-medium shadow-lg border border-white/30"
                >
                  ログアウト
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className="px-4 py-2 rounded-lg hover:bg-white/10 transition font-medium"
                >
                  ログイン
                </Link>
                <Link
                  href="/signup"
                  className="ml-2 bg-white/20 hover:bg-white/30 backdrop-blur-sm px-5 py-2 rounded-lg transition font-medium shadow-lg border border-white/30"
                >
                  新規登録
                </Link>
              </>
            )}
          </nav>

          {/* モバイルメニューボタン */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-white/10 transition"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* モバイルナビゲーション */}
        {isMenuOpen && (
          <div className="md:hidden pb-4 space-y-2">
            {user ? (
              <>
                <Link
                  href="/dashboard"
                  className="block px-4 py-2 rounded-lg hover:bg-white/10 transition"
                  onClick={() => setIsMenuOpen(false)}
                >
                  ダッシュボード
                </Link>
                <Link
                  href="/chat"
                  className="block px-4 py-2 rounded-lg hover:bg-white/10 transition"
                  onClick={() => setIsMenuOpen(false)}
                >
                  チャット
                </Link>
                <Link
                  href="/profile"
                  className="block px-4 py-2 rounded-lg hover:bg-white/10 transition"
                  onClick={() => setIsMenuOpen(false)}
                >
                  マイページ
                </Link>
                <button
                  onClick={() => {
                    setIsMenuOpen(false)
                    handleLogout()
                  }}
                  className="w-full text-left px-4 py-2 rounded-lg bg-white/20 hover:bg-white/30 transition"
                >
                  ログアウト
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className="block px-4 py-2 rounded-lg hover:bg-white/10 transition"
                  onClick={() => setIsMenuOpen(false)}
                >
                  ログイン
                </Link>
                <Link
                  href="/signup"
                  className="block px-4 py-2 rounded-lg bg-white/20 hover:bg-white/30 transition"
                  onClick={() => setIsMenuOpen(false)}
                >
                  新規登録
                </Link>
              </>
            )}
          </div>
        )}
      </div>
    </header>
  )
}
