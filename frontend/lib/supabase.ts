/**
 * Supabaseクライアント設定
 * ブラウザとサーバーサイドの両方で使用可能
 * 注: 現在はFirebase認証を使用しているため、Supabaseは非推奨
 */
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

// Supabaseが設定されていない場合は警告のみ（ビルド時のエラーを回避）
if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('Supabase environment variables not configured. Using Firebase authentication instead.')
}

/**
 * Supabaseクライアント（ブラウザ用）
 * 認証情報はlocalStorageに自動保存
 * 注: 空の値でもクライアントを作成（実際には使用されない）
 */
export const supabase = supabaseUrl && supabaseAnonKey ? createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
  }
}) : null as any

/**
 * 現在のユーザー情報を取得
 * @returns ユーザー情報 or null
 */
export async function getCurrentUser() {
  const { data: { user }, error } = await supabase.auth.getUser()

  if (error) {
    console.error('Error getting user:', error)
    return null
  }

  return user
}

/**
 * Google OAuth ログイン
 * @param redirectTo リダイレクト先URL（デフォルト: /dashboard）
 */
export async function signInWithGoogle(redirectTo: string = '/dashboard') {
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${window.location.origin}${redirectTo}`,
    },
  })

  if (error) {
    console.error('Error signing in with Google:', error)
    throw error
  }
}

/**
 * ログアウト
 */
export async function signOut() {
  const { error } = await supabase.auth.signOut()

  if (error) {
    console.error('Error signing out:', error)
    throw error
  }
}

/**
 * 認証状態の変化を監視
 * @param callback 認証状態が変化した時のコールバック
 */
export function onAuthStateChange(callback: (event: string, session: any) => void) {
  return supabase.auth.onAuthStateChange(callback)
}

/**
 * JWTトークンを取得
 * @returns アクセストークン or null
 */
export async function getAccessToken(): Promise<string | null> {
  const { data: { session }, error } = await supabase.auth.getSession()

  if (error || !session) {
    return null
  }

  return session.access_token
}
