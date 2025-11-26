/**
 * アプリケーション設定
 * 環境変数を一元管理
 */

// API URL - ビルド時に設定される環境変数を使用
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

// Firebase設定
export const FIREBASE_CONFIG = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || '',
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || '',
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || '',
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || '',
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || '',
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || '',
};

// バージョン情報
export const VERSION_INFO = {
  version: process.env.NEXT_PUBLIC_VERSION || '0.0.0',
  buildTime: process.env.NEXT_PUBLIC_BUILD_TIME || '',
  gitCommit: process.env.NEXT_PUBLIC_GIT_COMMIT || '',
};

// デバッグ用：ビルド時の環境変数を確認
if (typeof window !== 'undefined') {
  console.log('[Config] API_URL:', API_URL);
  console.log('[Config] Firebase Project:', FIREBASE_CONFIG.projectId);
}