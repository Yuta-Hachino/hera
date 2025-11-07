/**
 * Firebase Authentication ヘルパー関数
 * Supabase Auth から移行
 */
import {
  signInWithPopup,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  User,
  signInAnonymously
} from 'firebase/auth'
import { auth, googleProvider } from './firebase'

/**
 * Google OAuth ログイン
 * @returns ログインしたユーザー情報
 */
export async function signInWithGoogle(): Promise<User> {
  try {
    const result = await signInWithPopup(auth, googleProvider)
    console.log('Google sign-in successful:', result.user.email)
    return result.user
  } catch (error: any) {
    console.error('Google sign-in error:', error)
    throw new Error(error.message || 'Google認証に失敗しました')
  }
}

/**
 * ゲストログイン（匿名認証）
 * @returns 匿名ユーザー情報
 */
export async function signInAsGuest(): Promise<User> {
  try {
    const result = await signInAnonymously(auth)
    console.log('Guest sign-in successful')
    return result.user
  } catch (error: any) {
    console.error('Guest sign-in error:', error)
    throw new Error(error.message || 'ゲストログインに失敗しました')
  }
}

/**
 * ログアウト
 */
export async function signOut(): Promise<void> {
  try {
    await firebaseSignOut(auth)
    console.log('Sign out successful')
  } catch (error: any) {
    console.error('Sign out error:', error)
    throw new Error(error.message || 'ログアウトに失敗しました')
  }
}

/**
 * 認証状態の変化を監視
 * @param callback 認証状態が変化した時のコールバック
 */
export function onAuthChange(callback: (user: User | null) => void) {
  return onAuthStateChanged(auth, callback)
}

/**
 * 現在のユーザーを取得
 * @returns 現在のユーザー情報 or null
 */
export function getCurrentUser(): User | null {
  return auth.currentUser
}

/**
 * Firebase ID トークンを取得（バックエンド認証用）
 * @returns IDトークン or null
 */
export async function getIdToken(): Promise<string | null> {
  const user = auth.currentUser
  if (!user) return null

  try {
    return await user.getIdToken()
  } catch (error) {
    console.error('Error getting ID token:', error)
    return null
  }
}

/**
 * ユーザー情報を取得
 * @returns ユーザー情報オブジェクト
 */
export function getUserInfo(user: User | null) {
  if (!user) return null

  return {
    uid: user.uid,
    email: user.email,
    displayName: user.displayName,
    photoURL: user.photoURL,
    isAnonymous: user.isAnonymous,
    providerId: user.providerData[0]?.providerId || 'anonymous'
  }
}