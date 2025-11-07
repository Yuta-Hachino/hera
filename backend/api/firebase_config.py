"""
Firebase/GCP設定と初期化
Supabaseから完全移行
"""
import os
import json
from typing import Optional
import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

# Firebase初期化フラグ
_initialized = False
_db = None
_bucket = None

def initialize_firebase():
    """Firebase Admin SDKを初期化"""
    global _initialized, _db, _bucket

    if _initialized:
        return _db, _bucket

    # モック環境での実行チェック
    if os.getenv('FIREBASE_MOCK', 'false').lower() == 'true':
        print("🔵 Running in MOCK mode - Firebase features will be simulated")
        _initialized = True
        return None, None

    try:
        # サービスアカウントキーのパスを取得
        service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')

        if service_account_path and os.path.exists(service_account_path):
            # サービスアカウントキーで初期化
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred, {
                'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', '')
            })
            print("✅ Firebase initialized with service account")
        else:
            # デフォルト認証で初期化（Cloud Run環境など）
            firebase_admin.initialize_app(options={
                'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', '')
            })
            print("✅ Firebase initialized with default credentials")

        # Firestoreクライアント取得
        _db = firestore.client()

        # Cloud Storageバケット取得
        bucket_name = os.getenv('GCS_BUCKET_NAME', os.getenv('FIREBASE_STORAGE_BUCKET', ''))
        if bucket_name:
            _bucket = storage.bucket(bucket_name)

        _initialized = True
        return _db, _bucket

    except Exception as e:
        print(f"⚠️  Firebase initialization failed: {str(e)}")
        print("⚠️  Running in fallback mode - some features may be limited")
        _initialized = True
        return None, None

def get_firestore_client():
    """Firestoreクライアントを取得"""
    db, _ = initialize_firebase()
    return db

def get_storage_bucket():
    """Cloud Storageバケットを取得"""
    _, bucket = initialize_firebase()
    return bucket

def verify_id_token(id_token: str) -> Optional[dict]:
    """
    Firebase IDトークンを検証

    Args:
        id_token: Firebase認証で発行されたIDトークン

    Returns:
        検証成功時はデコードされたトークン情報、失敗時はNone
    """
    if os.getenv('FIREBASE_MOCK', 'false').lower() == 'true':
        # モック環境では簡易的な検証
        return {
            'uid': 'mock-user-id',
            'email': 'mock@example.com',
            'name': 'Mock User',
            'firebase': {'sign_in_provider': 'mock'}
        }

    try:
        initialize_firebase()
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"Token verification failed: {str(e)}")
        return None

def get_user(uid: str) -> Optional[dict]:
    """
    FirebaseユーザーIDから情報取得

    Args:
        uid: Firebase User ID

    Returns:
        ユーザー情報
    """
    if os.getenv('FIREBASE_MOCK', 'false').lower() == 'true':
        return {
            'uid': uid,
            'email': f'{uid}@example.com',
            'display_name': 'Mock User'
        }

    try:
        initialize_firebase()
        user = auth.get_user(uid)
        return {
            'uid': user.uid,
            'email': user.email,
            'display_name': user.display_name,
            'photo_url': user.photo_url,
            'provider_id': user.provider_id
        }
    except Exception as e:
        print(f"Get user failed: {str(e)}")
        return None