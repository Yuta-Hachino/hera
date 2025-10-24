"""
実際のAPIサーバーをテストするクライアント
"""
import requests
import json
import time
import sys
import os

# API設定
API_BASE_URL = "http://localhost:8080"

def test_api_health():
    """APIヘルスチェック"""
    print("🔍 APIヘルスチェック...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ API正常")
            return True
        else:
            print(f"❌ API異常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API接続エラー: {e}")
        return False

def test_create_session():
    """セッション作成テスト"""
    print("📝 セッション作成...")
    try:
        response = requests.post(f"{API_BASE_URL}/api/sessions", timeout=10)
        if response.status_code == 200:
            data = response.json()
            session_id = data.get('session_id')
            print(f"✅ セッション作成成功: {session_id}")
            return session_id
        else:
            print(f"❌ セッション作成失敗: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ セッション作成エラー: {e}")
        return None

def test_send_message(session_id, message):
    """メッセージ送信テスト"""
    print(f"💬 メッセージ送信: {message}")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/sessions/{session_id}/messages",
            json={"message": message},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            reply = data.get('reply', '')
            print(f"✅ 応答受信: {reply}")
            return data
        else:
            print(f"❌ メッセージ送信失敗: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ メッセージ送信エラー: {e}")
        return None

def test_get_status(session_id):
    """セッション状態確認テスト"""
    print("📊 セッション状態確認...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/sessions/{session_id}/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ セッション状態取得成功")
            return data
        else:
            print(f"❌ セッション状態取得失敗: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ セッション状態取得エラー: {e}")
        return None

def test_complete_session(session_id):
    """セッション完了テスト"""
    print("🏁 セッション完了...")
    try:
        response = requests.post(f"{API_BASE_URL}/api/sessions/{session_id}/complete", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ セッション完了成功")
            return data
        else:
            print(f"❌ セッション完了失敗: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ セッション完了エラー: {e}")
        return None

def run_full_test():
    """フルテスト実行"""
    print("🚀 APIテスト開始")
    print("=" * 50)

    # 1. ヘルスチェック
    if not test_api_health():
        print("❌ APIサーバーが起動していません")
        return False

    # 2. セッション作成
    session_id = test_create_session()
    if not session_id:
        print("❌ セッション作成に失敗")
        return False

    # 3. メッセージ送信テスト
    test_messages = [
        "こんにちは、33歳のエンジニアです",
        "独身で、東京に住んでいます",
        "理想のパートナーは明るくて優しい人です",
        "パートナーの顔の特徴は、目が大きくて笑顔が素敵な人です",
        "私の性格は社交的で新しいことが好きです",
        "将来は女の子1人と男の子1人を希望しています"
    ]

    for i, message in enumerate(test_messages, 1):
        print(f"\n--- メッセージ {i} ---")
        result = test_send_message(session_id, message)
        if not result:
            print(f"❌ メッセージ {i} 送信失敗")
            return False
        time.sleep(1)  # 1秒待機

    # 4. セッション状態確認
    print(f"\n--- セッション状態確認 ---")
    status = test_get_status(session_id)
    if not status:
        print("❌ セッション状態確認失敗")
        return False

    # 5. セッション完了
    print(f"\n--- セッション完了 ---")
    complete = test_complete_session(session_id)
    if not complete:
        print("❌ セッション完了失敗")
        return False

    print("\n🎉 全テスト完了！")
    return True

if __name__ == "__main__":
    success = run_full_test()
    sys.exit(0 if success else 1)
