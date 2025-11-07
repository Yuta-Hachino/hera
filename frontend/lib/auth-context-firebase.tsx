/**
 * Firebase Authentication Context
 * Supabase から Firebase への移行版
 */
'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { User } from 'firebase/auth'
import {
  signInWithGoogle,
  signInAsGuest,
  signOut,
  onAuthChange,
  getCurrentUser,
  getIdToken,
  getUserInfo
} from './firebase-auth'

interface AuthContextType {
  user: User | null
  loading: boolean
  error: string | null
  signInWithGoogle: () => Promise<void>
  signInAsGuest: () => Promise<void>
  signOut: () => Promise<void>
  getIdToken: () => Promise<string | null>
  isAuthenticated: boolean
  userInfo: any
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 認証状態の監視
  useEffect(() => {
    const unsubscribe = onAuthChange((user) => {
      setUser(user)
      setLoading(false)
      setError(null)
    })

    // 初期ユーザー取得
    const currentUser = getCurrentUser()
    if (currentUser) {
      setUser(currentUser)
    }
    setLoading(false)

    return () => unsubscribe()
  }, [])

  // Google ログイン
  const handleGoogleSignIn = async () => {
    setError(null)
    setLoading(true)
    try {
      await signInWithGoogle()
    } catch (err: any) {
      setError(err.message)
      console.error('Google sign-in failed:', err)
    } finally {
      setLoading(false)
    }
  }

  // ゲストログイン
  const handleGuestSignIn = async () => {
    setError(null)
    setLoading(true)
    try {
      await signInAsGuest()
    } catch (err: any) {
      setError(err.message)
      console.error('Guest sign-in failed:', err)
    } finally {
      setLoading(false)
    }
  }

  // ログアウト
  const handleSignOut = async () => {
    setError(null)
    setLoading(true)
    try {
      await signOut()
    } catch (err: any) {
      setError(err.message)
      console.error('Sign out failed:', err)
    } finally {
      setLoading(false)
    }
  }

  const value: AuthContextType = {
    user,
    loading,
    error,
    signInWithGoogle: handleGoogleSignIn,
    signInAsGuest: handleGuestSignIn,
    signOut: handleSignOut,
    getIdToken,
    isAuthenticated: !!user,
    userInfo: getUserInfo(user)
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// カスタムフック
export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}