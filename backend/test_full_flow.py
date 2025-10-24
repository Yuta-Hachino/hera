#!/usr/bin/env python3
"""
Heraエージェントとのやりとりから家族フェーズまで一貫テスト
"""

import requests
import json
import time
import sys
import os

# API設定
API_BASE_URL = "http://localhost:8080"
ADK_BASE_URL = "http://localhost:8000"

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
    except requests.exceptions.RequestException as e:
        print(f"❌ API接続エラー: {e}")
        return False

def test_adk_health():
    """ADK Web UIヘルスチェック"""
    print("🔍 ADK Web UIヘルスチェック...")
    try:
        response = requests.get(f"{ADK_BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ ADK Web UI正常")
            return True
        else:
            print(f"❌ ADK Web UI異常: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ ADK Web UI接続エラー: {e}")
        return False

def create_session():
    """セッション作成"""
    print("📝 セッション作成...")
    try:
        response = requests.post(f"{API_BASE_URL}/api/sessions", timeout=10)
        if response.status_code == 200:
            data = response.json()
            session_id = data['session_id']
            print(f"✅ セッション作成成功: {session_id}")
            return session_id
        else:
            print(f"❌ セッション作成失敗: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ セッション作成エラー: {e}")
        return None

def send_message(session_id, message):
    """メッセージ送信"""
    print(f"💬 メッセージ送信: {message}")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/sessions/{session_id}/messages",
            json={"message": message},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 応答受信: {data.get('reply', '')}")
            return data
        else:
            print(f"❌ メッセージ送信失敗: {response.status_code}")
            print(f"エラー: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ メッセージ送信エラー: {e}")
        return None

def get_session_status(session_id):
    """セッション状態取得"""
    print("📊 セッション状態取得...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/sessions/{session_id}/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ プロファイル: {data.get('user_profile', {})}")
            print(f"✅ 進捗: {data.get('information_progress', {})}")
            return data
        else:
            print(f"❌ 状態取得失敗: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ 状態取得エラー: {e}")
        return None

def complete_session(session_id):
    """セッション完了"""
    print("🏁 セッション完了...")
    try:
        response = requests.post(f"{API_BASE_URL}/api/sessions/{session_id}/complete", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 完了: {data.get('message', '')}")
            print(f"✅ 完了状態: {data.get('information_complete', False)}")
            return data
        else:
            print(f"❌ セッション完了失敗: {response.status_code}")
            print(f"エラー: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ セッション完了エラー: {e}")
        return None

def test_image_upload(session_id):
    """画像アップロードテスト"""
    print("🖼️ 画像アップロードテスト...")
    try:
        # ダミー画像ファイルを作成
        from PIL import Image
        dummy_img = Image.new('RGB', (100, 100), color='red')
        dummy_path = f"/tmp/test_user_{session_id}.png"
        dummy_img.save(dummy_path)

        with open(dummy_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{API_BASE_URL}/api/sessions/{session_id}/photos/user",
                files=files,
                timeout=30
            )

        os.remove(dummy_path)  # クリーンアップ

        if response.status_code == 200:
            data = response.json()
            print(f"✅ 画像アップロード成功: {data.get('image_url', '')}")
            return True
        else:
            print(f"❌ 画像アップロード失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 画像アップロードエラー: {e}")
        return False

def test_image_generation(session_id):
    """画像生成テスト"""
    print("🎨 画像生成テスト...")
    try:
        # パートナー画像生成
        response = requests.post(
            f"{API_BASE_URL}/api/sessions/{session_id}/generate-image",
            json={"target": "partner"},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ パートナー画像生成成功: {data.get('image_url', '')}")
            return True
        else:
            print(f"❌ 画像生成失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 画像生成エラー: {e}")
        return False

def test_child_image_generation(session_id):
    """子ども画像生成テスト"""
    print("👶 子ども画像生成テスト...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/sessions/{session_id}/generate-child-image",
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 子ども画像生成成功: {data.get('image_url', '')}")
            return True
        else:
            print(f"❌ 子ども画像生成失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 子ども画像生成エラー: {e}")
        return False

def main():
    """メインテストフロー"""
    print("🚀 Heraエージェントから家族フェーズまで一貫テスト開始")
    print("=" * 60)

    # 1. ヘルスチェック
    if not test_api_health():
        print("❌ APIが起動していません。先にAPIサーバーを起動してください。")
        return False

    if not test_adk_health():
        print("❌ ADK Web UIが起動していません。先にADK Web UIを起動してください。")
        return False

    # 2. セッション作成
    session_id = create_session()
    if not session_id:
        print("❌ セッション作成に失敗しました。")
        return False

    # 3. Heraエージェントとの会話
    print("\n" + "=" * 60)
    print("🗣️ Heraエージェントとの会話テスト")
    print("=" * 60)

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
        result = send_message(session_id, message)
        if not result:
            print(f"❌ メッセージ {i} の送信に失敗しました。")
            return False
        time.sleep(1)  # 少し待機

    # 4. セッション状態確認
    print("\n" + "=" * 60)
    print("📊 セッション状態確認")
    print("=" * 60)

    status = get_session_status(session_id)
    if not status:
        print("❌ セッション状態の取得に失敗しました。")
        return False

    # 5. セッション完了
    print("\n" + "=" * 60)
    print("🏁 セッション完了")
    print("=" * 60)

    complete_result = complete_session(session_id)
    if not complete_result:
        print("❌ セッション完了に失敗しました。")
        return False

    # 6. 画像処理テスト
    print("\n" + "=" * 60)
    print("🖼️ 画像処理テスト")
    print("=" * 60)

    # 画像アップロード
    if not test_image_upload(session_id):
        print("⚠️ 画像アップロードに失敗しましたが、続行します。")

    # パートナー画像生成
    if not test_image_generation(session_id):
        print("⚠️ パートナー画像生成に失敗しましたが、続行します。")

    # 子ども画像生成
    if not test_child_image_generation(session_id):
        print("⚠️ 子ども画像生成に失敗しましたが、続行します。")

    # 7. 最終状態確認
    print("\n" + "=" * 60)
    print("📊 最終状態確認")
    print("=" * 60)

    final_status = get_session_status(session_id)
    if final_status:
        print("✅ 最終状態取得成功")
        print(f"プロファイル: {json.dumps(final_status.get('user_profile', {}), ensure_ascii=False, indent=2)}")
        print(f"進捗: {json.dumps(final_status.get('information_progress', {}), ensure_ascii=False, indent=2)}")

    print("\n" + "=" * 60)
    print("🎉 テスト完了！")
    print("=" * 60)
    print("✅ Heraエージェントとのやりとりから家族フェーズまで一貫してテストが完了しました。")
    print(f"セッションID: {session_id}")
    print("生成されたファイルは backend/tmp/user_sessions/ に保存されています。")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

