'use client'

/**
 * 認証が必要なページをラップするHOC
 * 未認証の場合はログインページにリダイレクト
 */
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from './auth-context-firebase'

export function withAuth<P extends object>(
  Component: React.ComponentType<P>
) {
  return function ProtectedRoute(props: P) {
    const { user, loading } = useAuth()
    const router = useRouter()

    useEffect(() => {
      if (!loading && !user) {
        // 未認証の場合はログインページにリダイレクト
        router.push('/login')
      }
    }, [user, loading, router])

    // ローディング中は何も表示しない
    if (loading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading...</p>
          </div>
        </div>
      )
    }

    // 未認証の場合は何も表示しない（リダイレクト中）
    if (!user) {
      return null
    }

    // 認証済みの場合はコンポーネントを表示
    return <Component {...props} />
  }
}
