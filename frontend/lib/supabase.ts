/**
 * Supabaseクライアント設定
 * ブラウザとサーバーサイドの両方で使用可能
 */
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

/**
 * Supabaseクライアント（ブラウザ用）
 * 認証情報はlocalStorageに自動保存
 */
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
  }
})

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
