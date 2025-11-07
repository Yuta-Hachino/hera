"""
Google Cloud Storage ベースのファイルストレージ
Supabase Storage から移行
"""
import os
import sys
import uuid
import base64
import json
from typing import Optional, BinaryIO, List, Dict, Any
from datetime import datetime, timedelta
from google.cloud import storage

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.storage_manager import StorageManager
from ..firebase_config import get_storage_bucket

class GCSStorageManager(StorageManager):
    """Google Cloud Storage を使用したファイル管理"""

    def __init__(self):
        """初期化"""
        self.bucket = get_storage_bucket()
        self.mock_mode = os.getenv('FIREBASE_MOCK', 'false').lower() == 'true'

        if self.mock_mode:
            # モック用のローカルストレージ
            self.mock_storage = {}
            self.mock_metadata = {}
            self.mock_storage_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'tmp', 'mock_storage')
            os.makedirs(self.mock_storage_dir, exist_ok=True)
            print("📌 GCSStorageManager: Running in MOCK mode")
        elif not self.bucket:
            print("⚠️  GCSStorageManager: Storage bucket not available")
            self.mock_mode = True
            self.mock_storage = {}
            self.mock_metadata = {}
            self.mock_storage_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'tmp', 'mock_storage')
            os.makedirs(self.mock_storage_dir, exist_ok=True)

    # ========== StorageManager Interface Implementation ==========

    def save_metadata(self, session_id: str, key: str, data: Dict[str, Any]) -> None:
        """
        メタデータを保存（StorageManager interface）

        Args:
            session_id: セッションID
            key: メタデータキー
            data: 保存するデータ
        """
        if self.mock_mode:
            if session_id not in self.mock_metadata:
                self.mock_metadata[session_id] = {}
            self.mock_metadata[session_id][key] = data
        else:
            try:
                # GCSにメタデータをJSONファイルとして保存
                metadata_path = f"sessions/{session_id}/metadata/{key}.json"
                blob = self.bucket.blob(metadata_path)
                blob.upload_from_string(
                    json.dumps(data, ensure_ascii=False),
                    content_type='application/json'
                )
            except Exception as e:
                print(f"Error saving metadata: {str(e)}")

    def load_metadata(self, session_id: str, key: str) -> Optional[Dict[str, Any]]:
        """
        メタデータを読み込み（StorageManager interface）

        Args:
            session_id: セッションID
            key: メタデータキー

        Returns:
            メタデータ、存在しない場合はNone
        """
        if self.mock_mode:
            session_meta = self.mock_metadata.get(session_id, {})
            return session_meta.get(key)

        try:
            metadata_path = f"sessions/{session_id}/metadata/{key}.json"
            blob = self.bucket.blob(metadata_path)
            if blob.exists():
                content = blob.download_as_text()
                return json.loads(content)
            return None
        except Exception as e:
            print(f"Error loading metadata: {str(e)}")
            return None

    def save_file(self, session_id: str, file_path: str, file_data: bytes) -> str:
        """
        ファイルを保存してURLを返す（StorageManager interface）

        Args:
            session_id: セッションID
            file_path: ファイルパス（例: 'photos/user.png'）
            file_data: ファイルデータ

        Returns:
            ファイルのURL
        """
        blob_name = f"sessions/{session_id}/{file_path}"

        if self.mock_mode:
            # モックモードではローカルに保存
            local_file_path = os.path.join(self.mock_storage_dir, blob_name.replace('/', '_'))
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            with open(local_file_path, 'wb') as f:
                f.write(file_data)

            if session_id not in self.mock_storage:
                self.mock_storage[session_id] = {}
            self.mock_storage[session_id][file_path] = local_file_path
            return f"/api/sessions/{session_id}/{file_path}"

        try:
            # Content-Typeを推測
            import mimetypes
            content_type, _ = mimetypes.guess_type(file_path)

            blob = self.bucket.blob(blob_name)
            blob.upload_from_string(file_data, content_type=content_type or 'application/octet-stream')

            # Signed URL を生成（1時間有効）
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=1),
                method="GET"
            )
            return url
        except Exception as e:
            print(f"Error saving file: {str(e)}")
            # フォールバックURLを返す
            return f"/api/sessions/{session_id}/{file_path}"

    def load_file(self, session_id: str, file_path: str) -> Optional[bytes]:
        """
        ファイルを読み込み（StorageManager interface）

        Args:
            session_id: セッションID
            file_path: ファイルパス（例: 'photos/user.png'）

        Returns:
            ファイルデータ、存在しない場合はNone
        """
        if self.mock_mode:
            session_files = self.mock_storage.get(session_id, {})
            local_file_path = session_files.get(file_path)
            if local_file_path and os.path.exists(local_file_path):
                with open(local_file_path, 'rb') as f:
                    return f.read()
            return None

        try:
            blob_name = f"sessions/{session_id}/{file_path}"
            blob = self.bucket.blob(blob_name)
            if blob.exists():
                return blob.download_as_bytes()
            return None
        except Exception as e:
            print(f"Error loading file: {str(e)}")
            return None

    def delete_session(self, session_id: str) -> None:
        """
        セッション全体を削除（StorageManager interface）

        Args:
            session_id: セッションID
        """
        if self.mock_mode:
            # モックストレージから削除
            if session_id in self.mock_storage:
                # ローカルファイルを削除
                for file_path, local_path in self.mock_storage[session_id].items():
                    if os.path.exists(local_path):
                        os.remove(local_path)
                del self.mock_storage[session_id]

            # メタデータを削除
            if session_id in self.mock_metadata:
                del self.mock_metadata[session_id]
        else:
            try:
                # セッションディレクトリ内のすべてのファイルを削除
                prefix = f"sessions/{session_id}/"
                blobs = self.bucket.list_blobs(prefix=prefix)
                for blob in blobs:
                    blob.delete()
            except Exception as e:
                print(f"Error deleting session: {str(e)}")

    # ========== Original Methods (互換性のため維持) ==========

    def upload_image(self, session_id: str, image_type: str, image_data: bytes,
                    content_type: str = 'image/png') -> Optional[str]:
        """
        画像アップロード（後方互換性のため維持）

        Args:
            session_id: セッションID
            image_type: 画像タイプ（'user', 'partner', 'child_1' など）
            image_data: 画像バイナリデータ
            content_type: コンテンツタイプ

        Returns:
            画像URL
        """
        file_path = f"images/{image_type}_{uuid.uuid4().hex[:8]}.png"
        return self.save_file(session_id, file_path, image_data)

    def upload_file(self, session_id: str, file_name: str, file_data: BinaryIO,
                   content_type: str = 'application/octet-stream') -> Optional[str]:
        """
        ファイルアップロード（後方互換性のため維持）

        Args:
            session_id: セッションID
            file_name: ファイル名
            file_data: ファイルデータ
            content_type: コンテンツタイプ

        Returns:
            ファイルURL
        """
        file_path = f"files/{file_name}"
        data = file_data.read()
        return self.save_file(session_id, file_path, data)

    def get_file_url(self, blob_name: str, expiration_hours: int = 1) -> Optional[str]:
        """
        ファイルURLを取得

        Args:
            blob_name: Blob名
            expiration_hours: URLの有効期限（時間）

        Returns:
            Signed URL
        """
        if self.mock_mode:
            # モックモードではダミーURLを返す
            return f"mock://storage/{blob_name}"

        try:
            blob = self.bucket.blob(blob_name)
            if not blob.exists():
                return None

            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=expiration_hours),
                method="GET"
            )
            return url
        except Exception as e:
            print(f"Error getting file URL: {str(e)}")
            return None

    def download_file(self, blob_name: str) -> Optional[bytes]:
        """
        ファイルダウンロード（パスを直接指定）

        Args:
            blob_name: Blob名

        Returns:
            ファイルバイナリデータ
        """
        # セッションIDとファイルパスを分割
        parts = blob_name.split('/')
        if len(parts) >= 3 and parts[0] == 'sessions':
            session_id = parts[1]
            file_path = '/'.join(parts[2:])
            return self.load_file(session_id, file_path)
        return None

    def delete_file(self, blob_name: str) -> bool:
        """
        ファイル削除

        Args:
            blob_name: Blob名

        Returns:
            成功/失敗
        """
        if self.mock_mode:
            # モックモードでの削除処理
            parts = blob_name.split('/')
            if len(parts) >= 3 and parts[0] == 'sessions':
                session_id = parts[1]
                file_path = '/'.join(parts[2:])
                if session_id in self.mock_storage and file_path in self.mock_storage[session_id]:
                    local_path = self.mock_storage[session_id][file_path]
                    if os.path.exists(local_path):
                        os.remove(local_path)
                    del self.mock_storage[session_id][file_path]
                    return True
            return False

        try:
            blob = self.bucket.blob(blob_name)
            blob.delete()
            return True
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            return False

    def list_files(self, prefix: str, limit: int = 100) -> List[str]:
        """
        ファイル一覧取得

        Args:
            prefix: プレフィックス
            limit: 取得件数

        Returns:
            ファイル名リスト
        """
        if self.mock_mode:
            files = []
            for session_id, session_files in self.mock_storage.items():
                for file_path in session_files.keys():
                    full_path = f"sessions/{session_id}/{file_path}"
                    if full_path.startswith(prefix):
                        files.append(full_path)
            return files[:limit]

        try:
            blobs = self.bucket.list_blobs(prefix=prefix, max_results=limit)
            return [blob.name for blob in blobs]
        except Exception as e:
            print(f"Error listing files: {str(e)}")
            return []

    def delete_session_files(self, session_id: str) -> bool:
        """
        セッションに関連するすべてのファイルを削除

        Args:
            session_id: セッションID

        Returns:
            成功/失敗
        """
        self.delete_session(session_id)
        return True