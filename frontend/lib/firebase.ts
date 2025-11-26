/**
 * Firebase Authentication設定
 * Google OAuth認証とJWTトークン管理
 */
import { initializeApp, getApps, FirebaseApp } from 'firebase/app'
import {
  getAuth,
  signInWithPopup,
  GoogleAuthProvider,
  signOut as firebaseSignOut,
  onAuthStateChanged as firebaseOnAuthStateChanged,
  User,
  Auth,
} from 'firebase/auth'

// Firebase設定
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
}

// Firebase初期化（クライアントサイドのみ）
let app: FirebaseApp
let auth: Auth

if (typeof window !== 'undefined') {
  // すでに初期化されている場合は既存のappを使用
  if (!getApps().length) {
    app = initializeApp(firebaseConfig)
  } else {
    app = getApps()[0]
  }
  auth = getAuth(app)
}

/**
 * Google OAuth プロバイダー
 */
const googleProvider = new GoogleAuthProvider()

/**
 * 現在のユーザー情報を取得
 * @returns ユーザー情報 or null
 */
export async function getCurrentUser(): Promise<User | null> {
  if (typeof window === 'undefined') {
    return null
  }

  return new Promise((resolve) => {
    const unsubscribe = firebaseOnAuthStateChanged(auth, (user) => {
      unsubscribe()
      resolve(user)
    })
  })
}

/**
 * Google OAuth ログイン
 * @param redirectTo リダイレクト先URL（デフォルト: /dashboard）
 */
export async function signInWithGoogle(redirectTo: string = '/dashboard') {
  if (typeof window === 'undefined') {
    throw new Error('signInWithGoogle can only be called on the client side')
  }

  try {
    const result = await signInWithPopup(auth, googleProvider)
    console.log('Google sign-in successful:', result.user.email)

    // リダイレクトはNext.jsのルーターで処理
    // window.location.href = redirectTo
  } catch (error: any) {
    console.error('Error signing in with Google:', error)
    throw error
  }
}

/**
 * ログアウト
 */
export async function signOut() {
  if (typeof window === 'undefined') {
    throw new Error('signOut can only be called on the client side')
  }

  try {
    await firebaseSignOut(auth)
    console.log('Sign out successful')
  } catch (error) {
    console.error('Error signing out:', error)
    throw error
  }
}

/**
 * 認証状態の変化を監視
 * @param callback 認証状態が変化した時のコールバック
 */
export function onAuthStateChange(callback: (user: User | null) => void) {
  if (typeof window === 'undefined') {
    return { unsubscribe: () => {} }
  }

  const unsubscribe = firebaseOnAuthStateChanged(auth, callback)
  return { unsubscribe }
}

/**
 * JWTトークンを取得
 * @returns アクセストークン or null
 */
export async function getAccessToken(): Promise<string | null> {
  if (typeof window === 'undefined') {
    return null
  }

  const user = auth.currentUser
  if (!user) {
    return null
  }

  try {
    const token = await user.getIdToken()
    return token
  } catch (error) {
    console.error('Error getting access token:', error)
    return null
  }
}

export { auth }
