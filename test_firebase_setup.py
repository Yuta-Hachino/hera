#!/usr/bin/env python3
"""
Firebase/GCP移行のテストスクリプト
モックモードで動作確認
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.api.firebase_config import initialize_firebase, verify_id_token, get_user
from backend.api.session.firebase_session_manager import FirebaseSessionManager
from backend.api.storage.gcs_storage import GCSStorageManager

def test_firebase_config():
    """Firebase設定のテスト"""
    print("\n🔍 Testing Firebase Configuration...")

    db, bucket = initialize_firebase()

    if os.getenv('FIREBASE_MOCK', 'false').lower() == 'true':
        print("✅ Running in MOCK mode - Firebase features simulated")
    else:
        if db:
            print("✅ Firestore client initialized")
        else:
            print("⚠️  Firestore client not available")

        if bucket:
            print("✅ Storage bucket initialized")
        else:
            print("⚠️  Storage bucket not available")

    # モックトークンの検証テスト
    print("\n🔍 Testing ID Token Verification...")
    mock_token = "mock-id-token"
    decoded = verify_id_token(mock_token)
    if decoded:
        print(f"✅ Token verified: {decoded}")
    else:
        print("⚠️  Token verification failed")

    # モックユーザー取得テスト
    print("\n🔍 Testing User Retrieval...")
    user_info = get_user("mock-user-id")
    if user_info:
        print(f"✅ User retrieved: {user_info}")
    else:
        print("⚠️  User retrieval failed")

def test_session_manager():
    """セッション管理のテスト"""
    print("\n🔍 Testing Session Manager...")

    manager = FirebaseSessionManager()

    # セッション作成
    print("Creating new session...")
    session_id = manager.create_session(user_id="test-user")
    print(f"✅ Session created: {session_id}")

    # セッション取得
    print("Retrieving session...")
    session = manager.get_session(session_id)
    if session:
        print(f"✅ Session retrieved: {session}")
    else:
        print("⚠️  Session retrieval failed")

    # プロファイル保存
    print("Saving profile...")
    profile = {
        "name": "テストユーザー",
        "age": 30,
        "hobbies": ["読書", "映画鑑賞"]
    }
    if manager.save_profile(session_id, profile):
        print("✅ Profile saved")
    else:
        print("⚠️  Profile save failed")

    # 会話追加
    print("Adding conversation...")
    if manager.add_conversation(session_id, "こんにちは", "user"):
        print("✅ Conversation added")
    else:
        print("⚠️  Conversation add failed")

    # 会話取得
    print("Retrieving conversations...")
    conversations = manager.get_conversations(session_id)
    if conversations:
        print(f"✅ Conversations retrieved: {len(conversations)} messages")
    else:
        print("⚠️  No conversations found")

def test_storage_manager():
    """ストレージ管理のテスト"""
    print("\n🔍 Testing Storage Manager...")

    manager = GCSStorageManager()

    # テスト用画像データ
    test_image = b"fake-image-data"

    # 画像アップロード
    print("Uploading test image...")
    url = manager.upload_image("test-session", "test-image", test_image)
    if url:
        print(f"✅ Image uploaded: {url}")
    else:
        print("⚠️  Image upload failed")

    # ファイルリスト取得
    print("Listing files...")
    files = manager.list_files("sessions/test-session/")
    if files:
        print(f"✅ Files found: {files}")
    else:
        print("⚠️  No files found")

def main():
    """メインテスト実行"""
    print("=" * 60)
    print("🚀 Firebase/GCP Migration Test Suite")
    print("=" * 60)

    # 環境変数の確認
    print("\n📋 Environment Check:")
    print(f"FIREBASE_MOCK: {os.getenv('FIREBASE_MOCK', 'false')}")
    print(f"GEMINI_API_KEY: {'✅ Set' if os.getenv('GEMINI_API_KEY') else '❌ Not set'}")
    print(f"PYTHONPATH: {os.getenv('PYTHONPATH', 'Not set')}")

    # 各テストを実行
    test_firebase_config()
    test_session_manager()
    test_storage_manager()

    print("\n" + "=" * 60)
    print("✨ All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    # 環境変数を読み込み
    from dotenv import load_dotenv
    load_dotenv('backend/.env')

    main()