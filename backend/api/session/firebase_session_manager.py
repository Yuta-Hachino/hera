"""
Firestore ベースのセッション管理
Supabase PostgreSQL から移行
"""
import os
import sys
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, List, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.session_manager import SessionManager
from google.cloud import firestore
from ..firebase_config import get_firestore_client

class FirebaseSessionManager(SessionManager):
    """Firestore を使用したセッション管理"""

    def __init__(self):
        """初期化"""
        self.db = get_firestore_client()
        self.mock_mode = os.getenv('FIREBASE_MOCK', 'false').lower() == 'true'

        # フォールバック用に常にmock_storageを初期化
        self.mock_storage = {}

        if self.mock_mode:
            print("📌 FirebaseSessionManager: Running in MOCK mode")
        elif not self.db:
            print("⚠️  FirebaseSessionManager: Firestore client not available")
            self.mock_mode = True

    # ========== SessionManager Interface Implementation ==========

    def save(self, session_id: str, data: Dict[str, Any]) -> None:
        """
        セッションデータを保存（SessionManager interface）

        Args:
            session_id: セッションID
            data: 保存するデータのディクショナリ
        """
        if self.mock_mode:
            if session_id not in self.mock_storage:
                self.mock_storage[session_id] = {'sessionId': session_id}

            for key, value in data.items():
                if key == 'user_profile':
                    self.save_profile(session_id, value)
                elif key == 'conversation_history':
                    # 既存の会話履歴をクリアして新規保存
                    if 'conversations' not in self.mock_storage[session_id]:
                        self.mock_storage[session_id]['conversations'] = {}
                    self.mock_storage[session_id]['conversations']['main'] = []
                    if isinstance(value, list):
                        for conv in value:
                            self.add_conversation(
                                session_id,
                                conv.get('message', ''),
                                conv.get('speaker', 'user'),
                                'main'
                            )
                elif key == 'family_conversation':
                    # 家族会話履歴
                    if 'conversations' not in self.mock_storage[session_id]:
                        self.mock_storage[session_id]['conversations'] = {}
                    self.mock_storage[session_id]['conversations']['family'] = []
                    if isinstance(value, list):
                        for conv in value:
                            self.add_conversation(
                                session_id,
                                conv.get('message', ''),
                                conv.get('speaker', 'user'),
                                'family'
                            )
                else:
                    # その他のデータはそのまま保存
                    self.mock_storage[session_id][key] = value
        else:
            try:
                # Firestoreにデータを保存
                session_ref = self.db.collection('sessions').document(session_id)

                # セッションが存在しない場合は作成
                if not session_ref.get().exists:
                    session_ref.set({
                        'sessionId': session_id,
                        'createdAt': datetime.now().isoformat(),
                        'updatedAt': datetime.now().isoformat(),
                        'status': 'active'
                    })

                # 各データタイプに応じて保存
                for key, value in data.items():
                    if key == 'user_profile':
                        self.save_profile(session_id, value)
                    elif key == 'conversation_history':
                        # 既存の会話履歴をクリアして新規保存
                        conv_ref = session_ref.collection('conversations')
                        # 既存のドキュメントを削除
                        for doc in conv_ref.stream():
                            doc.reference.delete()
                        # 新規保存
                        if isinstance(value, list):
                            for idx, conv in enumerate(value):
                                conv_data = {
                                    'message': conv.get('message', ''),
                                    'speaker': conv.get('speaker', 'user'),
                                    'timestamp': conv.get('timestamp', datetime.now().isoformat()),
                                    'orderIndex': idx
                                }
                                conv_ref.add(conv_data)
                    elif key == 'family_conversation':
                        # 家族会話履歴
                        fam_conv_ref = session_ref.collection('familyConversations')
                        # 既存のドキュメントを削除
                        for doc in fam_conv_ref.stream():
                            doc.reference.delete()
                        # 新規保存
                        if isinstance(value, list):
                            for idx, conv in enumerate(value):
                                conv_data = {
                                    'message': conv.get('message', ''),
                                    'speaker': conv.get('speaker', 'user'),
                                    'timestamp': conv.get('timestamp', datetime.now().isoformat()),
                                    'orderIndex': idx
                                }
                                fam_conv_ref.add(conv_data)
                    else:
                        # 重要なフラグやメタデータはメインドキュメントに保存
                        # （クエリでフィルタリングできるように）
                        main_document_fields = [
                            'completed', 'completed_at', 'user_id', 'created_at',
                            'letter', 'family_image_url', 'status'
                        ]

                        if key in main_document_fields:
                            # メインドキュメントに直接保存
                            session_ref.update({key: value})
                        else:
                            # その他のデータはメタデータサブコレクションに保存
                            meta_ref = session_ref.collection('metadata').document(key)
                            meta_ref.set({'value': value})

                            # family_planの場合、letterとfamily_image_urlを抽出してメインドキュメントに保存
                            if key == 'family_plan' and isinstance(value, dict):
                                if 'letter' in value:
                                    session_ref.update({'letter': value['letter']})
                                # family_image_urlは家族写真のURL（後で画像生成時に保存される）

                # 更新日時を更新
                session_ref.update({'updatedAt': datetime.now().isoformat()})
            except Exception as e:
                print(f"Error saving session data: {str(e)}")
                # フォールバックとしてモックストレージに保存
                if session_id not in self.mock_storage:
                    self.mock_storage[session_id] = {'sessionId': session_id}
                for key, value in data.items():
                    self.mock_storage[session_id][key] = value

    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        セッションデータを読み込み（SessionManager interface）

        Args:
            session_id: セッションID

        Returns:
            セッションデータのディクショナリ、存在しない場合はNone
        """
        if self.mock_mode:
            if session_id not in self.mock_storage:
                return None

            session_data = self.mock_storage[session_id].copy()
            result = {}

            # プロファイル
            if 'profile' in session_data:
                result['user_profile'] = session_data['profile']

            # 会話履歴
            if 'conversations' in session_data:
                if 'main' in session_data['conversations']:
                    result['conversation_history'] = session_data['conversations']['main']
                if 'family' in session_data['conversations']:
                    result['family_conversation'] = session_data['conversations']['family']

            # その他のメタデータ
            for key in ['created_at', 'status', 'family_trip_info', 'family_plan']:
                if key in session_data:
                    result[key] = session_data[key]

            return result

        try:
            session_ref = self.db.collection('sessions').document(session_id)
            session_doc = session_ref.get()

            if not session_doc.exists:
                return None

            result = {}

            # プロファイル取得
            profile = self.get_profile(session_id)
            if profile:
                result['user_profile'] = profile

            # 会話履歴取得
            conversations = self.get_conversations(session_id, 'main')
            if conversations:
                result['conversation_history'] = conversations

            # 家族会話履歴取得
            family_conversations = self.get_conversations(session_id, 'family')
            if family_conversations:
                result['family_conversation'] = family_conversations

            # メタデータ取得
            metadata_ref = session_ref.collection('metadata')
            for doc in metadata_ref.stream():
                doc_data = doc.to_dict()
                if 'value' in doc_data:
                    result[doc.id] = doc_data['value']

            # セッションの基本情報（メインドキュメントから読み込み）
            session_data = session_doc.to_dict()
            result['created_at'] = session_data.get('createdAt')
            result['status'] = session_data.get('status')

            # メインドキュメントに保存されているフィールドを読み込み
            main_document_fields = [
                'completed', 'completed_at', 'user_id',
                'letter', 'family_image_url'
            ]
            for field in main_document_fields:
                if field in session_data:
                    result[field] = session_data[field]

            return result

        except Exception as e:
            print(f"Error loading session data: {str(e)}")
            return None

    def delete(self, session_id: str) -> None:
        """
        セッションデータを削除（SessionManager interface）

        Args:
            session_id: セッションID
        """
        self.delete_session(session_id)

    def exists(self, session_id: str) -> bool:
        """
        セッションが存在するか確認（SessionManager interface）

        Args:
            session_id: セッションID

        Returns:
            存在する場合True
        """
        if self.mock_mode:
            return session_id in self.mock_storage

        try:
            session_ref = self.db.collection('sessions').document(session_id)
            return session_ref.get().exists
        except Exception as e:
            print(f"Error checking session existence: {str(e)}")
            return session_id in self.mock_storage

    # ========== Original Methods ==========

    def create_session(self, user_id: Optional[str] = None) -> str:
        """
        新規セッション作成

        Args:
            user_id: Firebase User ID（オプション）

        Returns:
            セッションID
        """
        session_id = str(uuid.uuid4())
        session_data = {
            'sessionId': session_id,
            'userId': user_id or 'guest',
            'createdAt': datetime.now().isoformat(),
            'updatedAt': datetime.now().isoformat(),
            'status': 'active'
        }

        if self.mock_mode:
            self.mock_storage[session_id] = session_data
        else:
            try:
                self.db.collection('sessions').document(session_id).set(session_data)
            except Exception as e:
                print(f"Error creating session: {str(e)}")
                # フォールバック
                self.mock_storage[session_id] = session_data

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        セッション取得

        Args:
            session_id: セッションID

        Returns:
            セッションデータ
        """
        if self.mock_mode:
            return self.mock_storage.get(session_id)

        try:
            doc = self.db.collection('sessions').document(session_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting session: {str(e)}")
            return self.mock_storage.get(session_id)

    def update_session(self, session_id: str, data: Dict) -> bool:
        """
        セッション更新

        Args:
            session_id: セッションID
            data: 更新データ

        Returns:
            成功/失敗
        """
        data['updatedAt'] = datetime.now().isoformat()

        if self.mock_mode:
            if session_id in self.mock_storage:
                self.mock_storage[session_id].update(data)
                return True
            return False

        try:
            self.db.collection('sessions').document(session_id).update(data)
            return True
        except Exception as e:
            print(f"Error updating session: {str(e)}")
            if session_id in self.mock_storage:
                self.mock_storage[session_id].update(data)
                return True
            return False

    def save_profile(self, session_id: str, profile_data: Dict) -> bool:
        """
        プロファイル保存

        Args:
            session_id: セッションID
            profile_data: プロファイルデータ

        Returns:
            成功/失敗
        """
        if self.mock_mode:
            if session_id not in self.mock_storage:
                return False
            self.mock_storage[session_id]['profile'] = profile_data
            return True

        try:
            profile_ref = self.db.collection('sessions').document(session_id).collection('profiles').document('main')
            profile_ref.set(profile_data, merge=True)
            return True
        except Exception as e:
            print(f"Error saving profile: {str(e)}")
            return False

    def get_profile(self, session_id: str) -> Optional[Dict]:
        """
        プロファイル取得

        Args:
            session_id: セッションID

        Returns:
            プロファイルデータ
        """
        if self.mock_mode:
            session = self.mock_storage.get(session_id, {})
            return session.get('profile')

        try:
            profile_ref = self.db.collection('sessions').document(session_id).collection('profiles').document('main')
            doc = profile_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting profile: {str(e)}")
            return None

    def add_conversation(self, session_id: str, message: str, speaker: str,
                        conversation_type: str = 'main') -> bool:
        """
        会話履歴追加

        Args:
            session_id: セッションID
            message: メッセージ
            speaker: 話者
            conversation_type: 会話タイプ（'main' or 'family'）

        Returns:
            成功/失敗
        """
        conversation_data = {
            'message': message,
            'speaker': speaker,
            'timestamp': datetime.now().isoformat(),
            'orderIndex': self._get_next_order_index(session_id, conversation_type)
        }

        if self.mock_mode:
            if session_id not in self.mock_storage:
                return False
            if 'conversations' not in self.mock_storage[session_id]:
                self.mock_storage[session_id]['conversations'] = {}
            if conversation_type not in self.mock_storage[session_id]['conversations']:
                self.mock_storage[session_id]['conversations'][conversation_type] = []
            self.mock_storage[session_id]['conversations'][conversation_type].append(conversation_data)
            return True

        try:
            collection_name = 'conversations' if conversation_type == 'main' else 'familyConversations'
            conv_ref = self.db.collection('sessions').document(session_id).collection(collection_name)
            conv_ref.add(conversation_data)
            return True
        except Exception as e:
            print(f"Error adding conversation: {str(e)}")
            return False

    def get_conversations(self, session_id: str, conversation_type: str = 'main') -> List[Dict]:
        """
        会話履歴取得

        Args:
            session_id: セッションID
            conversation_type: 会話タイプ

        Returns:
            会話履歴リスト
        """
        if self.mock_mode:
            session = self.mock_storage.get(session_id, {})
            conversations = session.get('conversations', {}).get(conversation_type, [])
            return sorted(conversations, key=lambda x: x.get('orderIndex', 0))

        try:
            collection_name = 'conversations' if conversation_type == 'main' else 'familyConversations'
            conv_ref = self.db.collection('sessions').document(session_id).collection(collection_name)
            docs = conv_ref.order_by('orderIndex').get()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"Error getting conversations: {str(e)}")
            return []

    def _get_next_order_index(self, session_id: str, conversation_type: str) -> int:
        """
        次の会話順序インデックスを取得

        Args:
            session_id: セッションID
            conversation_type: 会話タイプ

        Returns:
            次のインデックス
        """
        conversations = self.get_conversations(session_id, conversation_type)
        if not conversations:
            return 0
        return max(c.get('orderIndex', 0) for c in conversations) + 1

    def complete_session(self, session_id: str) -> bool:
        """
        セッション完了

        Args:
            session_id: セッションID

        Returns:
            成功/失敗
        """
        return self.update_session(session_id, {'status': 'completed'})

    def delete_session(self, session_id: str) -> bool:
        """
        セッション削除

        Args:
            session_id: セッションID

        Returns:
            成功/失敗
        """
        if self.mock_mode:
            if session_id in self.mock_storage:
                del self.mock_storage[session_id]
                return True
            return False

        try:
            # サブコレクションも含めて削除
            session_ref = self.db.collection('sessions').document(session_id)

            # サブコレクションを削除
            for collection_name in ['profiles', 'conversations', 'familyConversations', 'metadata']:
                collection_ref = session_ref.collection(collection_name)
                for doc in collection_ref.stream():
                    doc.reference.delete()

            # メインドキュメントを削除
            session_ref.delete()
            return True
        except Exception as e:
            print(f"Error deleting session: {str(e)}")
            return False

    def list_sessions(self, user_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        セッション一覧取得

        Args:
            user_id: ユーザーID（フィルタリング用）
            limit: 取得件数

        Returns:
            セッションリスト
        """
        if self.mock_mode:
            sessions = list(self.mock_storage.values())
            if user_id:
                sessions = [s for s in sessions if s.get('userId') == user_id]
            return sorted(sessions, key=lambda x: x.get('createdAt', ''), reverse=True)[:limit]

        try:
            query = self.db.collection('sessions').order_by('createdAt', direction=firestore.Query.DESCENDING).limit(limit)

            if user_id:
                query = query.where('userId', '==', user_id)

            docs = query.get()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"Error listing sessions: {str(e)}")
            return []