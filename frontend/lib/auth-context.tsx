'use client'

/**
 * 認証コンテキスト
 * アプリ全体で認証状態を管理
 */
import { createContext, useContext, useEffect, useState } from 'react'
import { User } from 'firebase/auth'
import { getCurrentUser, signOut as firebaseSignOut, onAuthStateChange } from './firebase'

interface AuthContextType {
  user: User | null
  loading: boolean
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  signOut: async () => {},
})

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // 初回マウント時にユーザー情報を取得
    getCurrentUser().then((user) => {
      setUser(user)
      setLoading(false)
    })

    // 認証状態の変化を監視
    const { unsubscribe } = onAuthStateChange((user) => {
      setUser(user)
      setLoading(false)
    })

    return () => {
      unsubscribe()
    }
  }, [])

  const handleSignOut = async () => {
    await firebaseSignOut()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, signOut: handleSignOut }}>
      {children}
    </AuthContext.Provider>
  )
}

/**
 * 認証コンテキストを使用するカスタムフック
 */
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
