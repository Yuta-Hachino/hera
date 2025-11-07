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


class SupabaseSessionManager(SessionManager):
    """Supabaseベースのセッション管理（本番環境用）"""

    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Args:
            supabase_url: SupabaseプロジェクトのURL
            supabase_key: Supabaseのサービスロールキー
        """
        try:
            from supabase import create_client, Client
        except ImportError:
            raise ImportError(
                "Supabaseセッション管理を使用するには、supabaseパッケージが必要です。\n"
                "pip install supabase をして実行してください。"
            )

        self.client: Client = create_client(supabase_url, supabase_key)

    def save(self, session_id: str, data: Dict[str, Any]) -> None:
        """セッションデータをSupabaseに保存"""
        # セッションが存在するか確認
        session_response = self.client.table('sessions').select('id').eq('session_id', session_id).execute()

        if not session_response.data:
            # セッションが存在しない場合は作成
            self.client.table('sessions').insert({
                'session_id': session_id,
                'status': 'active',
                'updated_at': datetime.now().isoformat()
            }).execute()

        # 各データタイプに応じて保存
        for key, value in data.items():
            if key == 'user_profile':
                # user_profilesテーブルに保存
                profile_response = self.client.table('user_profiles').select('id').eq('session_id', session_id).execute()
                if profile_response.data:
                    # 更新
                    self.client.table('user_profiles').update(value).eq('session_id', session_id).execute()
                else:
                    # 新規作成
                    profile_data = {'session_id': session_id, **value}
                    self.client.table('user_profiles').insert(profile_data).execute()

            elif key == 'conversation_history':
                # conversation_historyテーブルに保存（既存削除→新規挿入）
                self.client.table('conversation_history').delete().eq('session_id', session_id).execute()
                if isinstance(value, list):
                    for idx, conv in enumerate(value):
                        conv_data = {
                            'session_id': session_id,
                            'message': conv.get('message', ''),
                            'speaker': conv.get('speaker', 'user'),
                            'order_index': idx,
                            'timestamp': conv.get('timestamp', datetime.now().isoformat())
                        }
                        self.client.table('conversation_history').insert(conv_data).execute()

            elif key == 'family_conversation':
                # family_conversationsテーブルに保存
                self.client.table('family_conversations').delete().eq('session_id', session_id).execute()
                if isinstance(value, list):
                    for idx, conv in enumerate(value):
                        conv_data = {
                            'session_id': session_id,
                            'message': conv.get('message', ''),
                            'speaker': conv.get('speaker', 'user'),
                            'order_index': idx,
                            'timestamp': conv.get('timestamp', datetime.now().isoformat())
                        }
                        self.client.table('family_conversations').insert(conv_data).execute()

            elif key == 'family_trip_info':
                # family_trip_infoテーブルに保存
                trip_response = self.client.table('family_trip_info').select('id').eq('session_id', session_id).execute()
                trip_data = {
                    'session_id': session_id,
                    'destination': value.get('destination'),
                    'activities': value.get('activities', []),
                    'trip_data': value
                }
                if trip_response.data:
                    self.client.table('family_trip_info').update(trip_data).eq('session_id', session_id).execute()
                else:
                    self.client.table('family_trip_info').insert(trip_data).execute()

            elif key == 'family_plan':
                # family_plansテーブルに保存
                plan_response = self.client.table('family_plans').select('id').eq('session_id', session_id).execute()
                plan_data = {
                    'session_id': session_id,
                    'destination': value.get('destination'),
                    'activities': value.get('activities', []),
                    'story': value.get('story'),
                    'letter': value.get('letter'),
                    'plan_data': value
                }
                if plan_response.data:
                    self.client.table('family_plans').update(plan_data).eq('session_id', session_id).execute()
                else:
                    self.client.table('family_plans').insert(plan_data).execute()

        # セッションの更新日時を更新
        self.client.table('sessions').update({
            'updated_at': datetime.now().isoformat()
        }).eq('session_id', session_id).execute()

    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """セッションデータをSupabaseから読み込み"""
        # セッションが存在するか確認
        session_response = self.client.table('sessions').select('*').eq('session_id', session_id).execute()

        if not session_response.data:
            return None

        data = {}

        # user_profilesから読み込み
        profile_response = self.client.table('user_profiles').select('*').eq('session_id', session_id).execute()
        if profile_response.data:
            profile = profile_response.data[0]
            # session_id, id, created_at を除外
            data['user_profile'] = {k: v for k, v in profile.items()
                                   if k not in ['id', 'session_id', 'created_at', 'updated_at']}

        # conversation_historyから読み込み
        conv_response = self.client.table('conversation_history').select('*').eq('session_id', session_id).order('order_index').execute()
        if conv_response.data:
            data['conversation_history'] = [
                {
                    'message': conv['message'],
                    'speaker': conv['speaker'],
                    'timestamp': conv.get('timestamp')
                }
                for conv in conv_response.data
            ]

        # family_conversationsから読み込み
        family_conv_response = self.client.table('family_conversations').select('*').eq('session_id', session_id).order('order_index').execute()
        if family_conv_response.data:
            data['family_conversation'] = [
                {
                    'message': conv['message'],
                    'speaker': conv['speaker'],
                    'timestamp': conv.get('timestamp')
                }
                for conv in family_conv_response.data
            ]

        # family_trip_infoから読み込み
        trip_response = self.client.table('family_trip_info').select('*').eq('session_id', session_id).execute()
        if trip_response.data:
            data['family_trip_info'] = trip_response.data[0].get('trip_data', {})

        # family_plansから読み込み
        plan_response = self.client.table('family_plans').select('*').eq('session_id', session_id).execute()
        if plan_response.data:
            data['family_plan'] = plan_response.data[0].get('plan_data', {})

        # その他のメタデータ
        data['created_at'] = session_response.data[0].get('created_at')
        data['status'] = session_response.data[0].get('status')

        return data

    def delete(self, session_id: str) -> None:
        """セッションデータを削除（カスケード削除により関連データも削除）"""
        self.client.table('sessions').delete().eq('session_id', session_id).execute()

    def exists(self, session_id: str) -> bool:
        """セッションが存在するか確認"""
        response = self.client.table('sessions').select('id').eq('session_id', session_id).execute()
        return len(response.data) > 0


def create_session_manager() -> SessionManager:
    """
    環境変数に基づいてセッションマネージャーを作成

    環境変数:
        SESSION_TYPE: 'file', 'redis', 'supabase', 'firebase' (デフォルト: 'file')
        REDIS_URL: RedisのURL（SESSION_TYPE='redis'の場合に必須）
        SUPABASE_URL: SupabaseプロジェクトのURL（SESSION_TYPE='supabase'の場合に必須）
        SUPABASE_SERVICE_ROLE_KEY: Supabaseサービスロールキー（SESSION_TYPE='supabase'の場合に必須）
        FIREBASE_MOCK: FirebaseをMockモードで実行するか（SESSION_TYPE='firebase'の場合）
        SESSIONS_DIR: ファイルベースの場合のセッションディレクトリ

    Returns:
        SessionManager: セッション管理オブジェクト
    """
    session_type = os.getenv('SESSION_TYPE', 'file').lower()

    if session_type == 'firebase':
        # Firebase/Firestoreベースのセッションマネージャーを使用
        # api.session.firebase_session_manager のクラスを直接インポート
        from api.session.firebase_session_manager import FirebaseSessionManager as FBSessionManager
        return FBSessionManager()

    elif session_type == 'supabase':
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        if not supabase_url or not supabase_key:
            raise ValueError(
                "SESSION_TYPE='supabase'の場合、SUPABASE_URLとSUPABASE_SERVICE_ROLE_KEY環境変数が必要です。"
            )
        return SupabaseSessionManager(supabase_url, supabase_key)

    elif session_type == 'redis':
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
