"""
Gemini Live API Connection Test

このテストファイルは、Gemini Live API統合の基礎機能をテストします。

テスト内容:
1. EphemeralTokenManagerの初期化
2. トークン生成
3. WebSocket URL生成
4. トークンの形式検証

注意: このテストは実際のAPI呼び出しを行うため、GEMINI_API_KEYが必要です。
"""

import os
import pytest
from datetime import datetime, timezone
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()


class TestEphemeralTokenManager:
    """EphemeralTokenManagerのテスト"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """テストセットアップ"""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            pytest.skip("GEMINI_API_KEY環境変数が設定されていません")

    def test_import_ephemeral_token_manager(self):
        """EphemeralTokenManagerのインポートテスト"""
        from utils.ephemeral_token_manager import EphemeralTokenManager
        assert EphemeralTokenManager is not None

    def test_create_manager_instance(self):
        """マネージャーインスタンス作成テスト"""
        from utils.ephemeral_token_manager import EphemeralTokenManager

        manager = EphemeralTokenManager(api_key=self.api_key)
        assert manager is not None
        assert manager.api_key == self.api_key
        assert manager.api_version == 'v1alpha'

    def test_get_singleton_instance(self):
        """シングルトンインスタンス取得テスト"""
        from utils.ephemeral_token_manager import get_ephemeral_token_manager

        manager1 = get_ephemeral_token_manager(api_key=self.api_key)
        manager2 = get_ephemeral_token_manager()

        # 同じインスタンスであることを確認
        assert manager1 is manager2

    def test_websocket_url_generation(self):
        """WebSocket URL生成テスト"""
        from utils.ephemeral_token_manager import EphemeralTokenManager

        manager = EphemeralTokenManager(api_key=self.api_key)
        test_token = "test_token_12345"
        ws_url = manager.get_websocket_url(test_token)

        assert ws_url.startswith("wss://generativelanguage.googleapis.com/ws")
        assert "BidiGenerateContent" in ws_url
        assert test_token in ws_url

    @pytest.mark.skipif(
        os.getenv('SKIP_LIVE_API_TESTS', 'false').lower() == 'true',
        reason="Live APIテストをスキップ（SKIP_LIVE_API_TESTS=true）"
    )
    def test_create_ephemeral_token(self):
        """
        Ephemeralトークン生成テスト（実際のAPI呼び出し）

        注意: このテストは実際にGemini APIを呼び出します。
        スキップする場合は環境変数 SKIP_LIVE_API_TESTS=true を設定してください。
        """
        from utils.ephemeral_token_manager import EphemeralTokenManager

        manager = EphemeralTokenManager(api_key=self.api_key)

        try:
            token_data = manager.create_token(
                model='gemini-2.0-flash-live-preview-04-09'
            )

            # トークンデータの検証
            assert 'token' in token_data
            assert 'expire_time' in token_data
            assert 'api_version' in token_data
            assert token_data['token'] is not None
            assert len(token_data['token']) > 0

            # 有効期限の検証（未来であることを確認）
            now = datetime.now(tz=timezone.utc)
            expire_time = token_data['expire_time']
            assert expire_time > now

            print(f"✅ トークン生成成功: {token_data['token'][:20]}...")
            print(f"✅ 有効期限: {expire_time}")

        except Exception as e:
            pytest.fail(f"トークン生成失敗: {e}")

    @pytest.mark.skipif(
        os.getenv('SKIP_LIVE_API_TESTS', 'false').lower() == 'true',
        reason="Live APIテストをスキップ（SKIP_LIVE_API_TESTS=true）"
    )
    def test_create_token_with_convenience_function(self):
        """
        便利関数を使ったトークン生成テスト

        注意: このテストは実際にGemini APIを呼び出します。
        """
        from utils.ephemeral_token_manager import create_ephemeral_token

        try:
            token_data = create_ephemeral_token(model='gemini-2.0-flash-live-preview-04-09')

            assert 'token' in token_data
            assert 'expire_time' in token_data
            assert token_data['token'] is not None

            print(f"✅ 便利関数でトークン生成成功: {token_data['token'][:20]}...")

        except Exception as e:
            pytest.fail(f"トークン生成失敗: {e}")


class TestLiveAPIEndpoint:
    """Live APIエンドポイントのテスト"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """テストセットアップ"""
        # 環境変数チェック
        if not os.getenv('GEMINI_API_KEY'):
            pytest.skip("GEMINI_API_KEY環境変数が設定されていません")

    def test_live_mode_disabled_by_default(self):
        """Live API機能がデフォルトで無効であることを確認"""
        # 環境変数がdisabledまたは未設定の場合
        live_mode = os.getenv('GEMINI_LIVE_MODE', 'disabled').lower()
        assert live_mode == 'disabled', "Live API機能はデフォルトで無効であるべき"

    def test_audio_input_disabled_by_default(self):
        """音声入力がデフォルトで無効であることを確認"""
        audio_input_enabled = os.getenv('AUDIO_INPUT_ENABLED', 'false').lower()
        assert audio_input_enabled == 'false', "音声入力はデフォルトで無効であるべき"


def main():
    """
    このスクリプトを直接実行した場合のテスト

    使用方法:
        python tests/test_live_api_connection.py
    """
    print("=" * 60)
    print("Gemini Live API Connection Test")
    print("=" * 60)

    # 環境変数チェック
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ エラー: GEMINI_API_KEY環境変数が設定されていません")
        print("設定方法: export GEMINI_API_KEY='your-api-key'")
        return 1

    print(f"✅ GEMINI_API_KEY: 設定済み（{api_key[:10]}...）")

    # Live API機能確認
    live_mode = os.getenv('GEMINI_LIVE_MODE', 'disabled')
    print(f"📊 GEMINI_LIVE_MODE: {live_mode}")

    # 音声設定確認
    audio_input = os.getenv('AUDIO_INPUT_ENABLED', 'false')
    print(f"🎤 AUDIO_INPUT_ENABLED: {audio_input}")

    # EphemeralTokenManagerテスト
    print("\n" + "-" * 60)
    print("EphemeralTokenManagerテスト開始...")
    print("-" * 60)

    try:
        from utils.ephemeral_token_manager import EphemeralTokenManager

        manager = EphemeralTokenManager(api_key=api_key)
        print("✅ EphemeralTokenManager初期化成功")

        # WebSocket URL生成テスト
        test_token = "test_token_123"
        ws_url = manager.get_websocket_url(test_token)
        print(f"✅ WebSocket URL生成成功: {ws_url[:80]}...")

        # 実際のトークン生成（SKIP_LIVE_API_TESTS=falseの場合のみ）
        if os.getenv('SKIP_LIVE_API_TESTS', 'false').lower() != 'true':
            print("\n🔑 Ephemeralトークン生成中...")
            token_data = manager.create_token(model='gemini-2.0-flash-live-preview-04-09')
            print(f"✅ トークン生成成功!")
            print(f"   Token: {token_data['token'][:30]}...")
            print(f"   Expire: {token_data['expire_time']}")
        else:
            print("ℹ️ 実際のトークン生成はスキップされました（SKIP_LIVE_API_TESTS=true）")

        print("\n" + "=" * 60)
        print("✅ すべてのテストが成功しました！")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
