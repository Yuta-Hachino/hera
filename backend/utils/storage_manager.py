"""
ストレージ管理モジュール
メタデータ（Redis）と画像ファイル（S3/GCS）の統合管理
"""
import os
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, BinaryIO
from datetime import datetime
import mimetypes


class StorageManager(ABC):
    """ストレージ管理の基底クラス"""

    @abstractmethod
    def save_metadata(self, session_id: str, key: str, data: Dict[str, Any]) -> None:
        """メタデータを保存"""
        pass

    @abstractmethod
    def load_metadata(self, session_id: str, key: str) -> Optional[Dict[str, Any]]:
        """メタデータを読み込み"""
        pass

    @abstractmethod
    def save_file(self, session_id: str, file_path: str, file_data: bytes) -> str:
        """ファイルを保存してURLを返す"""
        pass

    @abstractmethod
    def load_file(self, session_id: str, file_path: str) -> Optional[bytes]:
        """ファイルを読み込み"""
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> None:
        """セッション全体を削除"""
        pass


class FirebaseStorageManager(StorageManager):
    """Firebase Storage + Firestore管理（本番用）"""

    def __init__(self, bucket_name: str = None):
        """
        Args:
            bucket_name: Firebase Storageのバケット名
        """
        try:
            import firebase_admin
            from firebase_admin import firestore, storage
        except ImportError:
            raise ImportError("pip install firebase-admin が必要です")

        # Firebase Storageクライアント（Firebase Admin SDK経由）
        self.bucket_name = bucket_name or os.getenv('FIREBASE_STORAGE_BUCKET')
        if not self.bucket_name:
            raise ValueError("FIREBASE_STORAGE_BUCKETが設定されていません")

        # Firebase Admin SDKからStorageバケットを取得
        self.bucket = storage.bucket(self.bucket_name)

        # Firestoreクライアント（メタデータ保存用）
        self.db = firestore.client()

    def _get_metadata_ref(self, session_id: str, key: str):
        """メタデータのFirestoreリファレンスを取得"""
        return self.db.collection('storage_metadata').document(session_id).collection('items').document(key)

    def _get_blob_path(self, session_id: str, file_path: str) -> str:
        """Firebase Storageのblobパスを取得"""
        return f"sessions/{session_id}/{file_path}"

    def save_metadata(self, session_id: str, key: str, data: Dict[str, Any]) -> None:
        """メタデータをFirestoreに保存"""
        ref = self._get_metadata_ref(session_id, key)
        ref.set({
            'data': data,
            'updated_at': datetime.utcnow().isoformat()
        })

    def load_metadata(self, session_id: str, key: str) -> Optional[Dict[str, Any]]:
        """メタデータをFirestoreから読み込み"""
        ref = self._get_metadata_ref(session_id, key)
        doc = ref.get()
        if not doc.exists:
            return None
        return doc.to_dict().get('data')

    def save_file(self, session_id: str, file_path: str, file_data: bytes) -> str:
        """ファイルをFirebase Storageに保存してURLを返す"""
        blob_path = self._get_blob_path(session_id, file_path)
        blob = self.bucket.blob(blob_path)

        # Content-Typeを推測
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type:
            blob.content_type = content_type

        # ファイルをアップロード
        blob.upload_from_string(file_data)

        # 公開URLを返す
        # Firebase Storageの場合: https://firebasestorage.googleapis.com/v0/b/{bucket}/o/{path}?alt=media
        return f"https://firebasestorage.googleapis.com/v0/b/{self.bucket_name}/o/{blob_path.replace('/', '%2F')}?alt=media"

    def load_file(self, session_id: str, file_path: str) -> Optional[bytes]:
        """ファイルをFirebase Storageから読み込み"""
        blob_path = self._get_blob_path(session_id, file_path)
        blob = self.bucket.blob(blob_path)

        if not blob.exists():
            return None

        return blob.download_as_bytes()

    def delete_session(self, session_id: str) -> None:
        """セッション全体を削除（メタデータとファイル）"""
        # Firestoreのメタデータを削除
        batch = self.db.batch()
        metadata_ref = self.db.collection('storage_metadata').document(session_id)
        items = metadata_ref.collection('items').stream()
        for item in items:
            batch.delete(item.reference)
        batch.delete(metadata_ref)
        batch.commit()

        # Firebase Storageのファイルを削除
        prefix = f"sessions/{session_id}/"
        blobs = self.bucket.list_blobs(prefix=prefix)
        for blob in blobs:
            blob.delete()


class LocalStorageManager(StorageManager):
    """ローカルストレージ管理（開発用）"""

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def _get_session_dir(self, session_id: str) -> str:
        return os.path.join(self.base_dir, session_id)

    def save_metadata(self, session_id: str, key: str, data: Dict[str, Any]) -> None:
        session_dir = self._get_session_dir(session_id)
        os.makedirs(session_dir, exist_ok=True)

        file_path = os.path.join(session_dir, f"{key}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_metadata(self, session_id: str, key: str) -> Optional[Dict[str, Any]]:
        file_path = os.path.join(self._get_session_dir(session_id), f"{key}.json")
        if not os.path.exists(file_path):
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_file(self, session_id: str, file_path: str, file_data: bytes) -> str:
        full_path = os.path.join(self._get_session_dir(session_id), file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'wb') as f:
            f.write(file_data)

        return f"/api/sessions/{session_id}/{file_path}"

    def load_file(self, session_id: str, file_path: str) -> Optional[bytes]:
        full_path = os.path.join(self._get_session_dir(session_id), file_path)
        if not os.path.exists(full_path):
            return None

        with open(full_path, 'rb') as f:
            return f.read()

    def delete_session(self, session_id: str) -> None:
        import shutil
        session_dir = self._get_session_dir(session_id)
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)


class CloudStorageManager(StorageManager):
    """クラウドストレージ管理（本番用）"""

    def __init__(self, redis_url: str, storage_type: str, **storage_config):
        """
        Args:
            redis_url: RedisのURL（メタデータ保存用）
            storage_type: 's3', 'gcs', または 'azure'
            storage_config: ストレージ固有の設定
        """
        # Redisクライアント（メタデータ用）
        try:
            import redis
        except ImportError:
            raise ImportError("pip install redis が必要です")

        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.storage_type = storage_type
        self.storage_config = storage_config

        # ストレージクライアントの初期化
        if storage_type == 's3':
            self._init_s3()
        elif storage_type == 'gcs':
            self._init_gcs()
        elif storage_type == 'azure':
            self._init_azure()
        else:
            raise ValueError(f"未対応のストレージタイプ: {storage_type}")

    def _init_s3(self):
        """AWS S3の初期化"""
        try:
            import boto3
        except ImportError:
            raise ImportError("pip install boto3 が必要です")

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.storage_config.get('access_key'),
            aws_secret_access_key=self.storage_config.get('secret_key'),
            region_name=self.storage_config.get('region', 'ap-northeast-1')
        )
        self.bucket_name = self.storage_config.get('bucket_name')

    def _init_gcs(self):
        """Google Cloud Storageの初期化"""
        try:
            from google.cloud import storage
        except ImportError:
            raise ImportError("pip install google-cloud-storage が必要です")

        self.gcs_client = storage.Client()
        self.bucket_name = self.storage_config.get('bucket_name')

    def _init_azure(self):
        """Azure Blob Storageの初期化"""
        try:
            from azure.storage.blob import BlobServiceClient
        except ImportError:
            raise ImportError("pip install azure-storage-blob が必要です")

        connection_string = self.storage_config.get('connection_string')
        self.blob_service = BlobServiceClient.from_connection_string(connection_string)
        self.container_name = self.storage_config.get('container_name')

    def _get_redis_key(self, session_id: str, key: str) -> str:
        return f"session:{session_id}:meta:{key}"

    def save_metadata(self, session_id: str, key: str, data: Dict[str, Any]) -> None:
        redis_key = self._get_redis_key(session_id, key)
        self.redis.setex(
            redis_key,
            86400,  # 24時間
            json.dumps(data, ensure_ascii=False)
        )

    def load_metadata(self, session_id: str, key: str) -> Optional[Dict[str, Any]]:
        redis_key = self._get_redis_key(session_id, key)
        data = self.redis.get(redis_key)
        return json.loads(data) if data else None

    def save_file(self, session_id: str, file_path: str, file_data: bytes) -> str:
        """ファイルをクラウドストレージに保存"""
        object_key = f"sessions/{session_id}/{file_path}"
        content_type, _ = mimetypes.guess_type(file_path)

        if self.storage_type == 's3':
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_data,
                ContentType=content_type or 'application/octet-stream'
            )
            # 署名付きURLまたは公開URLを返す
            url = f"https://{self.bucket_name}.s3.amazonaws.com/{object_key}"

        elif self.storage_type == 'gcs':
            bucket = self.gcs_client.bucket(self.bucket_name)
            blob = bucket.blob(object_key)
            blob.upload_from_string(file_data, content_type=content_type)
            url = f"https://storage.googleapis.com/{self.bucket_name}/{object_key}"

        elif self.storage_type == 'azure':
            blob_client = self.blob_service.get_blob_client(
                container=self.container_name,
                blob=object_key
            )
            blob_client.upload_blob(file_data, overwrite=True)
            url = blob_client.url

        # URLをメタデータとして保存
        self.save_metadata(session_id, f"file:{file_path}", {"url": url})

        return url

    def load_file(self, session_id: str, file_path: str) -> Optional[bytes]:
        """ファイルをクラウドストレージから読み込み"""
        object_key = f"sessions/{session_id}/{file_path}"

        try:
            if self.storage_type == 's3':
                response = self.s3_client.get_object(
                    Bucket=self.bucket_name,
                    Key=object_key
                )
                return response['Body'].read()

            elif self.storage_type == 'gcs':
                bucket = self.gcs_client.bucket(self.bucket_name)
                blob = bucket.blob(object_key)
                return blob.download_as_bytes()

            elif self.storage_type == 'azure':
                blob_client = self.blob_service.get_blob_client(
                    container=self.container_name,
                    blob=object_key
                )
                return blob_client.download_blob().readall()

        except Exception as e:
            print(f"ファイル読み込みエラー: {e}")
            return None

    def delete_session(self, session_id: str) -> None:
        """セッション全体を削除"""
        # Redisのメタデータを削除
        pattern = f"session:{session_id}:*"
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)

        # クラウドストレージのファイルを削除
        prefix = f"sessions/{session_id}/"

        if self.storage_type == 's3':
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            if 'Contents' in response:
                objects = [{'Key': obj['Key']} for obj in response['Contents']]
                self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': objects}
                )

        elif self.storage_type == 'gcs':
            bucket = self.gcs_client.bucket(self.bucket_name)
            blobs = bucket.list_blobs(prefix=prefix)
            for blob in blobs:
                blob.delete()

        elif self.storage_type == 'azure':
            container_client = self.blob_service.get_container_client(
                self.container_name
            )
            blobs = container_client.list_blobs(name_starts_with=prefix)
            for blob in blobs:
                container_client.delete_blob(blob.name)


def create_storage_manager() -> StorageManager:
    """環境変数に基づいてストレージマネージャーを作成"""
    storage_mode = os.getenv('STORAGE_MODE', 'local').lower()

    if storage_mode == 'local':
        from config import get_sessions_dir
        return LocalStorageManager(get_sessions_dir())

    elif storage_mode == 'firebase':
        bucket_name = os.getenv('FIREBASE_STORAGE_BUCKET')
        return FirebaseStorageManager(bucket_name=bucket_name)

    elif storage_mode == 'cloud':
        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            raise ValueError("STORAGE_MODE='cloud'の場合、REDIS_URLが必要です")

        storage_type = os.getenv('CLOUD_STORAGE_TYPE', 's3').lower()

        if storage_type == 's3':
            config = {
                'access_key': os.getenv('AWS_ACCESS_KEY_ID'),
                'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
                'region': os.getenv('AWS_REGION', 'ap-northeast-1'),
                'bucket_name': os.getenv('S3_BUCKET_NAME')
            }
        elif storage_type == 'gcs':
            config = {
                'bucket_name': os.getenv('GCS_BUCKET_NAME')
            }
        elif storage_type == 'azure':
            config = {
                'connection_string': os.getenv('AZURE_STORAGE_CONNECTION_STRING'),
                'container_name': os.getenv('AZURE_CONTAINER_NAME')
            }
        else:
            raise ValueError(f"未対応のストレージタイプ: {storage_type}")

        return CloudStorageManager(redis_url, storage_type, **config)

    else:
        raise ValueError(f"未対応のストレージモード: {storage_mode}")
