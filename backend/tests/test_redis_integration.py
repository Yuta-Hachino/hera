"""
Redis統合の統合テスト
"""
import os
import pytest
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.session_manager import RedisSessionManager, FileSessionManager


class TestRedisSessionManager:
    """RedisSessionManagerの統合テスト"""

    @pytest.fixture
    def redis_manager(self):
        """Redisセッションマネージャー（テスト用）"""
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        try:
            manager = RedisSessionManager(redis_url, ttl=60)  # 1分のTTL
            yield manager
            # クリーンアップ
            manager.redis.flushdb()
        except Exception as e:
            pytest.skip(f"Redis接続失敗: {e}")

    def test_save_and_load(self, redis_manager):
        """データの保存と読み込みテスト"""
        session_id = "test-session-001"
        test_data = {
            "user_profile": {"name": "太郎", "age": 30},
            "conversation_history": ["こんにちは", "はじめまして"]
        }

        # 保存
        redis_manager.save(session_id, test_data)

        # 読み込み
        loaded_data = redis_manager.load(session_id)

        assert loaded_data is not None
        assert loaded_data["user_profile"]["name"] == "太郎"
        assert loaded_data["user_profile"]["age"] == 30
        assert len(loaded_data["conversation_history"]) == 2

    def test_exists(self, redis_manager):
        """セッション存在確認テスト"""
        session_id = "test-session-002"

        # 存在しない
        assert not redis_manager.exists(session_id)

        # 保存
        redis_manager.save(session_id, {"test": "data"})

        # 存在する
        assert redis_manager.exists(session_id)

    def test_delete(self, redis_manager):
        """セッション削除テスト"""
        session_id = "test-session-003"

        # 保存
        redis_manager.save(session_id, {"test": "data"})
        assert redis_manager.exists(session_id)

        # 削除
        redis_manager.delete(session_id)
        assert not redis_manager.exists(session_id)

    def test_unicode_data(self, redis_manager):
        """日本語データの保存・読み込みテスト"""
        session_id = "test-session-004"
        test_data = {
            "user_profile": {
                "name": "山田太郎",
                "partner_name": "山田花子",
                "hobbies": ["読書", "料理", "旅行"]
            }
        }

        redis_manager.save(session_id, test_data)
        loaded_data = redis_manager.load(session_id)

        assert loaded_data["user_profile"]["name"] == "山田太郎"
        assert loaded_data["user_profile"]["partner_name"] == "山田花子"
        assert "読書" in loaded_data["user_profile"]["hobbies"]


class TestFileSessionManager:
    """FileSessionManagerの統合テスト"""

    @pytest.fixture
    def file_manager(self, tmp_path):
        """ファイルセッションマネージャー（テスト用）"""
        manager = FileSessionManager(str(tmp_path))
        yield manager

    def test_save_and_load(self, file_manager):
        """データの保存と読み込みテスト"""
        session_id = "test-session-101"
        test_data = {
            "user_profile": {"name": "太郎", "age": 30},
            "conversation_history": ["こんにちは", "はじめまして"]
        }

        # 保存
        file_manager.save(session_id, test_data)

        # 読み込み
        loaded_data = file_manager.load(session_id)

        assert loaded_data is not None
        assert loaded_data["user_profile"]["name"] == "太郎"
        assert loaded_data["user_profile"]["age"] == 30
        assert len(loaded_data["conversation_history"]) == 2

    def test_exists(self, file_manager):
        """セッション存在確認テスト"""
        session_id = "test-session-102"

        # 存在しない
        assert not file_manager.exists(session_id)

        # 保存
        file_manager.save(session_id, {"test": "data"})

        # 存在する
        assert file_manager.exists(session_id)

    def test_delete(self, file_manager):
        """セッション削除テスト"""
        session_id = "test-session-103"

        # 保存
        file_manager.save(session_id, {"test": "data"})
        assert file_manager.exists(session_id)

        # 削除
        file_manager.delete(session_id)
        assert not file_manager.exists(session_id)


class TestSessionManagerFactory:
    """セッションマネージャーファクトリーのテスト"""

    def test_create_file_session_manager(self, monkeypatch, tmp_path):
        """ファイルベースのマネージャー作成テスト"""
        monkeypatch.setenv('SESSION_TYPE', 'file')
        monkeypatch.setenv('SESSIONS_DIR', str(tmp_path))

        from utils.session_manager import create_session_manager
        manager = create_session_manager()

        assert isinstance(manager, FileSessionManager)

    def test_create_redis_session_manager(self, monkeypatch):
        """Redisベースのマネージャー作成テスト"""
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        monkeypatch.setenv('SESSION_TYPE', 'redis')
        monkeypatch.setenv('REDIS_URL', redis_url)

        from utils.session_manager import create_session_manager

        try:
            manager = create_session_manager()
            assert isinstance(manager, RedisSessionManager)
        except Exception as e:
            pytest.skip(f"Redis接続失敗: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
