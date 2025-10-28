"""
セッション管理モジュール
ファイルベースとRedisベースの両方をサポート
"""
import os
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime, timedelta


class SessionManager(ABC):
    """セッション管理の基底クラス"""

    @abstractmethod
    def save(self, session_id: str, data: Dict[str, Any]) -> None:
        """セッションデータを保存"""
        pass

    @abstractmethod
    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """セッションデータを読み込み"""
        pass

    @abstractmethod
    def delete(self, session_id: str) -> None:
        """セッションデータを削除"""
        pass

    @abstractmethod
    def exists(self, session_id: str) -> bool:
        """セッションが存在するか確認"""
        pass


class FileSessionManager(SessionManager):
    """ファイルベースのセッション管理（ローカル開発用）"""

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def _get_session_path(self, session_id: str) -> str:
        """セッションファイルのパスを取得"""
        return os.path.join(self.base_dir, session_id)

    def save(self, session_id: str, data: Dict[str, Any]) -> None:
        """セッションデータをファイルに保存"""
        session_dir = self._get_session_path(session_id)
        os.makedirs(session_dir, exist_ok=True)

        for key, value in data.items():
            file_path = os.path.join(session_dir, f"{key}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(value, f, ensure_ascii=False, indent=2)

    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """セッションデータをファイルから読み込み"""
        session_dir = self._get_session_path(session_id)
        if not os.path.exists(session_dir):
            return None

        data = {}
        for filename in os.listdir(session_dir):
            if filename.endswith('.json'):
                key = filename[:-5]  # .json を除去
                file_path = os.path.join(session_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data[key] = json.load(f)

        return data

    def delete(self, session_id: str) -> None:
        """セッションデータを削除"""
        import shutil
        session_dir = self._get_session_path(session_id)
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)

    def exists(self, session_id: str) -> bool:
        """セッションが存在するか確認"""
        return os.path.exists(self._get_session_path(session_id))


class RedisSessionManager(SessionManager):
    """Redisベースのセッション管理（本番環境用）"""

    def __init__(self, redis_url: str, ttl: int = 86400):
        """
        Args:
            redis_url: RedisのURL (例: redis://localhost:6379/0)
            ttl: セッションの有効期限（秒）デフォルト24時間
        """
        try:
            import redis
        except ImportError:
            raise ImportError(
                "Redisセッション管理を使用するには、redisパッケージが必要です。\n"
                "pip install redis をして実行してください。"
            )

        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.ttl = ttl

    def _get_key(self, session_id: str, field: str = None) -> str:
        """Redisキーを生成"""
        if field:
            return f"session:{session_id}:{field}"
        return f"session:{session_id}"

    def save(self, session_id: str, data: Dict[str, Any]) -> None:
        """セッションデータをRedisに保存"""
        for key, value in data.items():
            redis_key = self._get_key(session_id, key)
            self.redis.setex(
                redis_key,
                self.ttl,
                json.dumps(value, ensure_ascii=False)
            )

        # セッションのメタデータも保存
        meta_key = self._get_key(session_id, "_meta")
        self.redis.setex(
            meta_key,
            self.ttl,
            json.dumps({
                "created_at": datetime.now().isoformat(),
                "keys": list(data.keys())
            })
        )

    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """セッションデータをRedisから読み込み"""
        meta_key = self._get_key(session_id, "_meta")
        meta_data = self.redis.get(meta_key)

        if not meta_data:
            return None

        meta = json.loads(meta_data)
        data = {}

        for key in meta.get("keys", []):
            redis_key = self._get_key(session_id, key)
            value = self.redis.get(redis_key)
            if value:
                data[key] = json.loads(value)

        return data

    def delete(self, session_id: str) -> None:
        """セッションデータを削除"""
        # セッションに関連する全キーを取得
        pattern = self._get_key(session_id, "*")
        keys = self.redis.keys(pattern)

        if keys:
            self.redis.delete(*keys)

    def exists(self, session_id: str) -> bool:
        """セッションが存在するか確認"""
        meta_key = self._get_key(session_id, "_meta")
        return self.redis.exists(meta_key) > 0


def create_session_manager() -> SessionManager:
    """
    環境変数に基づいてセッションマネージャーを作成

    環境変数:
        SESSION_TYPE: 'file' または 'redis' (デフォルト: 'file')
        REDIS_URL: RedisのURL（SESSION_TYPE='redis'の場合に必須）
        SESSIONS_DIR: ファイルベースの場合のセッションディレクトリ

    Returns:
        SessionManager: セッション管理オブジェクト
    """
    session_type = os.getenv('SESSION_TYPE', 'file').lower()

    if session_type == 'redis':
        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            raise ValueError(
                "SESSION_TYPE='redis'の場合、REDIS_URL環境変数が必要です。"
            )
        ttl = int(os.getenv('SESSION_TTL', '86400'))  # デフォルト24時間
        return RedisSessionManager(redis_url, ttl=ttl)

    else:  # file
        from config import get_sessions_dir
        return FileSessionManager(get_sessions_dir())


# グローバルセッションマネージャー
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """グローバルセッションマネージャーを取得"""
    global _session_manager
    if _session_manager is None:
        _session_manager = create_session_manager()
    return _session_manager
