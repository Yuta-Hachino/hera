"""
Storage統合の統合テスト
"""
import os
import pytest
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.storage_manager import LocalStorageManager, create_storage_manager


class TestLocalStorageManager:
    """LocalStorageManagerの統合テスト"""

    @pytest.fixture
    def storage_manager(self, tmp_path):
        """ローカルストレージマネージャー（テスト用）"""
        manager = LocalStorageManager(str(tmp_path))
        yield manager

    def test_save_and_load_metadata(self, storage_manager):
        """メタデータの保存と読み込みテスト"""
        session_id = "test-session-201"
        metadata = {
            "image_url": "/api/sessions/test/photos/user.png",
            "uploaded_at": "2025-10-28T12:00:00"
        }

        # 保存
        storage_manager.save_metadata(session_id, "user_photo", metadata)

        # 読み込み
        loaded = storage_manager.load_metadata(session_id, "user_photo")

        assert loaded is not None
        assert loaded["image_url"] == metadata["image_url"]
        assert loaded["uploaded_at"] == metadata["uploaded_at"]

    def test_save_and_load_file(self, storage_manager):
        """ファイルの保存と読み込みテスト"""
        session_id = "test-session-202"
        file_path = "photos/test.png"

        # テスト用の画像データ（1x1の白い画像）
        from PIL import Image
        import io
        img = Image.new('RGB', (1, 1), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        file_data = img_bytes.getvalue()

        # 保存
        url = storage_manager.save_file(session_id, file_path, file_data)

        # 読み込み
        loaded_data = storage_manager.load_file(session_id, file_path)

        assert loaded_data is not None
        assert len(loaded_data) == len(file_data)
        assert loaded_data == file_data

    def test_delete_session(self, storage_manager):
        """セッション削除テスト"""
        session_id = "test-session-203"

        # メタデータとファイルを保存
        storage_manager.save_metadata(session_id, "test", {"foo": "bar"})
        storage_manager.save_file(session_id, "photos/test.png", b"test data")

        # セッション削除
        storage_manager.delete_session(session_id)

        # 確認
        assert storage_manager.load_metadata(session_id, "test") is None
        assert storage_manager.load_file(session_id, "photos/test.png") is None

    def test_multiple_files(self, storage_manager):
        """複数ファイルの保存テスト"""
        session_id = "test-session-204"

        files = {
            "photos/user.png": b"user image data",
            "photos/partner.png": b"partner image data",
            "photos/child_1.png": b"child image data"
        }

        # 複数ファイル保存
        for file_path, file_data in files.items():
            storage_manager.save_file(session_id, file_path, file_data)

        # 読み込み確認
        for file_path, expected_data in files.items():
            loaded_data = storage_manager.load_file(session_id, file_path)
            assert loaded_data == expected_data


class TestStorageManagerFactory:
    """ストレージマネージャーファクトリーのテスト"""

    def test_create_local_storage_manager(self, monkeypatch, tmp_path):
        """ローカルストレージマネージャー作成テスト"""
        monkeypatch.setenv('STORAGE_MODE', 'local')
        monkeypatch.setenv('SESSIONS_DIR', str(tmp_path))

        manager = create_storage_manager()
        assert isinstance(manager, LocalStorageManager)

    def test_create_cloud_storage_manager_s3(self, monkeypatch):
        """クラウドストレージマネージャー作成テスト（S3）"""
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        monkeypatch.setenv('STORAGE_MODE', 'cloud')
        monkeypatch.setenv('REDIS_URL', redis_url)
        monkeypatch.setenv('CLOUD_STORAGE_TYPE', 's3')
        monkeypatch.setenv('S3_BUCKET_NAME', 'test-bucket')
        monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'test-key')
        monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'test-secret')

        try:
            from utils.storage_manager import CloudStorageManager
            manager = create_storage_manager()
            assert isinstance(manager, CloudStorageManager)
            assert manager.storage_type == 's3'
        except ImportError:
            pytest.skip("boto3がインストールされていません")
        except Exception as e:
            pytest.skip(f"Redis接続失敗: {e}")


class TestImageProcessing:
    """画像処理の統合テスト"""

    def test_image_conversion(self):
        """PIL Image → Bytes変換テスト"""
        from PIL import Image
        import io

        # 画像作成
        img = Image.new('RGB', (100, 100), color='red')

        # Bytesに変換
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_data = img_bytes.getvalue()

        # 確認
        assert len(img_data) > 0
        assert img_data[:8] == b'\x89PNG\r\n\x1a\n'  # PNGマジックナンバー

        # Bytesから画像に戻す
        img_bytes2 = io.BytesIO(img_data)
        img2 = Image.open(img_bytes2)

        assert img2.size == (100, 100)
        assert img2.mode == 'RGB'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
