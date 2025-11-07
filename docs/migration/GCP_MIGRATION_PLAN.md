# Supabase から GCP マネージドサービスへの移行計画

## 📋 概要
Supabaseを完全に廃止し、GCPマネージドサービスに移行する詳細計画書です。

## 🎯 移行の目的
- 統一されたGCPエコシステムでの管理
- コストの最適化
- デプロイとメンテナンスの簡素化
- Cloud Runとの統合強化

## 🏗️ アーキテクチャ比較

### 現在のアーキテクチャ（Supabase）
```
┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│  Supabase   │
│  (Next.js)  │     │   (Auth)    │
└─────────────┘     └─────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌─────────────┐
│   Backend   │────▶│  Supabase   │
│  (Flask)    │     │(DB/Storage) │
└─────────────┘     └─────────────┘
```

### 新アーキテクチャ（GCP）
```
┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│  Firebase   │
│  (Next.js)  │     │    Auth     │
└─────────────┘     └─────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌─────────────┐
│   Backend   │────▶│  Firestore  │
│  (Flask)    │     └─────────────┘
└─────────────┘            │
       │                   ▼
       ▼            ┌─────────────┐
┌─────────────┐     │   Cloud     │
│  Cloud Run  │────▶│   Storage   │
└─────────────┘     └─────────────┘
```

## 🔄 サービスマッピング

| 現在（Supabase）          | 新（GCP）                    | 理由                           |
|---------------------------|------------------------------|--------------------------------|
| Supabase Auth             | Firebase Authentication      | Google OAuth統合が簡単          |
| Supabase Database         | Firestore                    | NoSQL、リアルタイム同期対応     |
| Supabase Storage          | Cloud Storage                | Cloud Runとの統合が簡単         |
| Supabase JWT              | Firebase Admin SDK           | トークン検証の簡素化            |
| Row Level Security (RLS)  | Firestore Security Rules     | より柔軟なルール設定            |

## 📝 データモデル移行

### 現在のテーブル構造（PostgreSQL）
```sql
-- sessions
- id (UUID)
- session_id (TEXT)
- user_id (UUID)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- status (TEXT)

-- user_profiles
- id (UUID)
- session_id (TEXT)
- name (TEXT)
- age (INTEGER)
- partner_name (TEXT)
- hobbies (JSONB)
- children (JSONB)

-- conversation_history
- id (UUID)
- session_id (TEXT)
- message (TEXT)
- speaker (TEXT)
- order_index (INTEGER)
- timestamp (TIMESTAMP)
```

### 新データ構造（Firestore）
```javascript
// コレクション: sessions
{
  sessionId: string,
  userId: string,
  createdAt: timestamp,
  updatedAt: timestamp,
  status: string,

  // サブコレクション: profiles
  profiles: {
    name: string,
    age: number,
    partnerName: string,
    hobbies: array,
    children: array
  },

  // サブコレクション: conversations
  conversations: [{
    message: string,
    speaker: string,
    orderIndex: number,
    timestamp: timestamp
  }],

  // サブコレクション: familyConversations
  familyConversations: [{
    message: string,
    speaker: string,
    orderIndex: number,
    timestamp: timestamp
  }]
}
```

## 🔧 実装詳細

### Phase 1: Firebase プロジェクト設定

1. **Firebaseプロジェクト作成**
```bash
# Firebase CLIインストール
npm install -g firebase-tools

# ログイン
firebase login

# プロジェクト初期化
firebase init
```

2. **必要なサービスの有効化**
- Firebase Authentication
- Cloud Firestore
- Cloud Storage
- Firebase Admin SDK

3. **Google OAuth設定**
```javascript
// Firebase Console で設定
// Authentication > Sign-in method > Google を有効化
```

### Phase 2: バックエンド移行

#### 2.1 新しい依存関係
```python
# requirements.txt に追加
firebase-admin==6.5.0
google-cloud-firestore==2.19.0
google-cloud-storage==2.18.2
```

#### 2.2 Firebase Admin初期化
```python
# backend/api/firebase_config.py
import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
import os

# サービスアカウントキーで初期化
cred = credentials.Certificate(os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH'))
firebase_admin.initialize_app(cred, {
    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
})

db = firestore.client()
bucket = storage.bucket()
```

#### 2.3 セッション管理の移行
```python
# backend/api/session/firebase_session_manager.py
from google.cloud import firestore
from datetime import datetime
import uuid

class FirebaseSessionManager:
    def __init__(self):
        self.db = firestore.Client()
        self.sessions = self.db.collection('sessions')

    def create_session(self, user_id: str = None) -> str:
        """新規セッション作成"""
        session_id = str(uuid.uuid4())
        session_data = {
            'sessionId': session_id,
            'userId': user_id,
            'createdAt': datetime.now(),
            'updatedAt': datetime.now(),
            'status': 'active'
        }

        self.sessions.document(session_id).set(session_data)
        return session_id

    def get_session(self, session_id: str):
        """セッション取得"""
        doc = self.sessions.document(session_id).get()
        if doc.exists:
            return doc.to_dict()
        return None

    def update_profile(self, session_id: str, profile_data: dict):
        """プロファイル更新"""
        profile_ref = self.sessions.document(session_id).collection('profiles').document('main')
        profile_ref.set(profile_data, merge=True)

    def add_conversation(self, session_id: str, message: str, speaker: str):
        """会話履歴追加"""
        conv_ref = self.sessions.document(session_id).collection('conversations')
        conv_ref.add({
            'message': message,
            'speaker': speaker,
            'timestamp': datetime.now(),
            'orderIndex': self._get_next_order_index(session_id, 'conversations')
        })
```

#### 2.4 ストレージ管理の移行
```python
# backend/api/storage/gcs_storage.py
from google.cloud import storage
import os
from typing import Optional

class GCSStorageManager:
    def __init__(self):
        self.bucket = storage.Client().bucket(os.getenv('GCS_BUCKET_NAME'))

    def upload_image(self, session_id: str, image_type: str, image_data: bytes) -> str:
        """画像アップロード"""
        blob_name = f"sessions/{session_id}/images/{image_type}.png"
        blob = self.bucket.blob(blob_name)

        blob.upload_from_string(image_data, content_type='image/png')
        blob.make_public()  # または signed URL を使用

        return blob.public_url

    def get_image_url(self, session_id: str, image_type: str) -> Optional[str]:
        """画像URL取得"""
        blob_name = f"sessions/{session_id}/images/{image_type}.png"
        blob = self.bucket.blob(blob_name)

        if blob.exists():
            return blob.public_url
        return None
```

### Phase 3: フロントエンド移行

#### 3.1 Firebase SDK導入
```bash
npm install firebase firebase-admin
npm uninstall @supabase/supabase-js
```

#### 3.2 Firebase初期化
```typescript
// frontend/lib/firebase.ts
import { initializeApp } from 'firebase/app'
import { getAuth, GoogleAuthProvider } from 'firebase/auth'
import { getFirestore } from 'firebase/firestore'
import { getStorage } from 'firebase/storage'

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID
}

const app = initializeApp(firebaseConfig)
export const auth = getAuth(app)
export const googleProvider = new GoogleAuthProvider()
export const db = getFirestore(app)
export const storage = getStorage(app)
```

#### 3.3 認証処理の移行
```typescript
// frontend/lib/firebase-auth.ts
import {
  signInWithPopup,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  User
} from 'firebase/auth'
import { auth, googleProvider } from './firebase'

export async function signInWithGoogle() {
  try {
    const result = await signInWithPopup(auth, googleProvider)
    return result.user
  } catch (error) {
    console.error('Google sign-in error:', error)
    throw error
  }
}

export async function signOut() {
  try {
    await firebaseSignOut(auth)
  } catch (error) {
    console.error('Sign out error:', error)
    throw error
  }
}

export function onAuthChange(callback: (user: User | null) => void) {
  return onAuthStateChanged(auth, callback)
}

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
```

### Phase 4: 環境変数更新

#### バックエンド (.env)
```env
# Firebase/GCP設定
FIREBASE_SERVICE_ACCOUNT_PATH=./service-account-key.json
GCP_PROJECT_ID=hera-production
GCS_BUCKET_NAME=hera-production-storage

# 既存の設定
GEMINI_API_KEY=your-key-here
FLASK_DEBUG=False
PORT=8080
```

#### フロントエンド (.env.local)
```env
# Firebase設定
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=hera-production.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=hera-production
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=hera-production.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
NEXT_PUBLIC_FIREBASE_APP_ID=your-app-id

# バックエンドAPI
NEXT_PUBLIC_API_URL=http://localhost:8080
```

## 🚀 移行手順

### Step 1: Firebase プロジェクト準備
```bash
# 1. Firebase Consoleでプロジェクト作成
# 2. 必要なサービスを有効化
# 3. サービスアカウントキーをダウンロード
# 4. Google OAuth を設定
```

### Step 2: バックエンドコード更新
```bash
# 1. 新しいブランチ作成
git checkout -b feature/gcp-migration

# 2. 依存関係更新
cd backend
pip install firebase-admin google-cloud-firestore google-cloud-storage

# 3. コード更新
# - session_manager.py を firebase_session_manager.py に置き換え
# - storage/__init__.py を gcs_storage.py に置き換え
```

### Step 3: フロントエンドコード更新
```bash
# 1. 依存関係更新
cd frontend
npm uninstall @supabase/supabase-js
npm install firebase

# 2. コード更新
# - lib/supabase.ts を lib/firebase.ts に置き換え
# - 認証処理を Firebase Auth に変更
```

### Step 4: ローカルテスト
```bash
# バックエンド起動
cd backend
python api/app.py

# フロントエンド起動
cd frontend
npm run dev
```

### Step 5: Cloud Run デプロイ
```bash
# Cloud Run 用の設定更新
./deploy-cloud-run.sh all
```

## ⏱️ 移行スケジュール

| フェーズ | タスク | 所要時間 |
|---------|--------|----------|
| Phase 1 | Firebase プロジェクト設定 | 1時間 |
| Phase 2 | バックエンド移行 | 3時間 |
| Phase 3 | フロントエンド移行 | 2時間 |
| Phase 4 | テスト・デバッグ | 2時間 |
| Phase 5 | デプロイ | 1時間 |
| **合計** | | **約9時間** |

## 💰 コスト比較

### 現在（Supabase Pro）
- Supabase Pro: $25/月
- 合計: $25/月

### 移行後（GCP）
- Firebase Auth: 無料枠内（5万MAU まで無料）
- Firestore: ~$5/月（100GBストレージ、100万読み取り/日）
- Cloud Storage: ~$2/月（10GB）
- Cloud Run: ~$10/月
- 合計: **約$17/月（32%削減）**

## ✅ 移行チェックリスト

- [ ] Firebase プロジェクト作成
- [ ] Firebase Auth 設定（Google OAuth）
- [ ] Firestore データベース作成
- [ ] Cloud Storage バケット作成
- [ ] サービスアカウントキー取得
- [ ] バックエンドコード移行
- [ ] フロントエンドコード移行
- [ ] 環境変数更新
- [ ] ローカルテスト完了
- [ ] Cloud Run デプロイ
- [ ] 本番環境動作確認
- [ ] Supabase プロジェクト削除

## 🔍 注意事項

1. **データ移行**: 既存のSupabaseデータは手動移行が必要
2. **ダウンタイム**: 移行中は一時的にサービス停止の可能性
3. **URLの変更**: 認証コールバックURLの更新が必要
4. **セキュリティルール**: Firestore Security Rulesの適切な設定
5. **バックアップ**: 移行前に必ずデータバックアップを取得

## 📚 参考資料

- [Firebase Documentation](https://firebase.google.com/docs)
- [Cloud Firestore Documentation](https://cloud.google.com/firestore/docs)
- [Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)