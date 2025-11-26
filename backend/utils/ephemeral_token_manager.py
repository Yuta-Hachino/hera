"""
Ephemeral Token Manager for Gemini Live API

このモジュールは、Gemini Live API用の短命認証トークン（Ephemeral Tokens）を
生成・管理するためのマネージャーを提供します。

セキュリティ:
- トークンは1回のみ使用可能（uses=1）
- デフォルト有効期限: 30分
- 新規セッション開始期限: 1分

参考: https://ai.google.dev/gemini-api/docs/ephemeral-tokens
"""

import os
import datetime
from typing import Dict, Any, Optional
from google import genai
from utils.logger import get_logger

logger = get_logger(__name__)


class EphemeralTokenManager:
    """
    Gemini Live API用のEphemeralトークンを生成・管理するクラス

    使用例:
        manager = EphemeralTokenManager(api_key="YOUR_API_KEY")
        token_data = manager.create_token()
        print(token_data['token'])
    """

    def __init__(
        self,
        api_key: str,
        api_version: str = 'v1alpha',
        expire_minutes: int = 30,
        new_session_expire_minutes: int = 1
    ):
        """
        Args:
            api_key: Gemini API Key
            api_version: APIバージョン（v1alpha または v1beta）
            expire_minutes: トークン有効期限（分）
            new_session_expire_minutes: 新規セッション開始期限（分）
        """
        self.api_key = api_key
        self.api_version = api_version
        self.expire_minutes = expire_minutes
        self.new_session_expire_minutes = new_session_expire_minutes

        # Google Generative AI クライアント初期化
        self.client = genai.Client(
            api_key=api_key,
            http_options={'api_version': api_version}
        )

        logger.info(f"✅ EphemeralTokenManager初期化完了（API version: {api_version}）")

    def create_token(
        self,
        model: Optional[str] = None,
        uses: int = 1,
        **config
    ) -> Dict[str, Any]:
        """
        Ephemeralトークンを生成

        Args:
            model: モデル名（オプション）
            uses: トークン使用回数（デフォルト: 1）
            **config: 追加の設定パラメータ

        Returns:
            Dict containing:
                - token: 生成されたトークン文字列
                - expire_time: 有効期限（ISO 8601形式）
                - new_session_expire_time: 新規セッション開始期限
                - model: モデル名（指定した場合）
                - api_version: APIバージョン

        Raises:
            Exception: トークン生成に失敗した場合
        """
        try:
            now = datetime.datetime.now(tz=datetime.timezone.utc)

            # トークン設定
            token_config = {
                'uses': uses,
                'expire_time': now + datetime.timedelta(minutes=self.expire_minutes),
                'new_session_expire_time': now + datetime.timedelta(minutes=self.new_session_expire_minutes),
                'http_options': {'api_version': self.api_version},
            }

            # カスタム設定をマージ
            token_config.update(config)

            # トークン生成
            logger.info(f"🔑 Ephemeralトークン生成開始（uses={uses}, expire={self.expire_minutes}分）")
            token_response = self.client.auth_tokens.create(config=token_config)

            # デバッグ: レスポンスの型と内容を確認
            logger.debug(f"Token response type: {type(token_response)}")
            logger.debug(f"Token response dir: {dir(token_response)}")
            if hasattr(token_response, '__dict__'):
                logger.debug(f"Token response __dict__: {token_response.__dict__}")

            # AuthToken(Pydanticモデル)では name に Ephemeral Token が格納される
            token_value = getattr(token_response, 'name', None)
            expire_time = getattr(token_response, 'expire_time', None)
            new_session_expire_time = getattr(token_response, 'new_session_expire_time', None)

            # SDK側仕様変更時のフォールバック
            if token_value is None:
                token_value = getattr(token_response, 'access_token', None)
            if token_value is None:
                token_value = getattr(token_response, 'auth_token', None)
            if token_value is None:
                token_value = getattr(token_response, 'value', None)
            if token_value is None and isinstance(token_response, str):
                token_value = token_response
            if token_value is None:
                token_str = str(token_response)
                if token_str and not token_str.startswith('<'):
                    token_value = token_str

            if expire_time is None:
                expire_time = getattr(token_response, 'expires_at', None)
            if expire_time is None:
                expire_time = token_config['expire_time']

            if new_session_expire_time is None:
                new_session_expire_time = getattr(token_response, 'new_session_expires_at', None)
            if new_session_expire_time is None:
                new_session_expire_time = token_config['new_session_expire_time']

            if token_value is None:
                raise ValueError('Ephemeral token value is missing in response')

            result = {
                'token': token_value,
                'expire_time': expire_time,
                'new_session_expire_time': new_session_expire_time,
                'api_version': self.api_version,
            }

            if model:
                result['model'] = model

            logger.info(f"✅ Ephemeralトークン生成成功（有効期限: {expire_time}）")
            return result

        except Exception as e:
            logger.error(f"❌ Ephemeralトークン生成失敗: {e}")
            raise Exception(f"トークン生成エラー: {str(e)}") from e

    def get_websocket_url(self, token: str) -> str:
        """
        WebSocket接続用のURLを生成

        Args:
            token: Ephemeralトークン

        Returns:
            WebSocket URL
        """
        base_url = "wss://generativelanguage.googleapis.com/ws"
        constrained = token.startswith('auth_tokens/')
        method = (
            "GenerativeService.BidiGenerateContentConstrained"
            if constrained
            else "GenerativeService.BidiGenerateContent"
        )
        service = f"google.ai.generativelanguage.{self.api_version}.{method}"

        ws_url = f"{base_url}/{service}?key={token}"

        logger.debug(f"🔗 WebSocket URL生成: {ws_url[:80]}...")
        return ws_url


# シングルトンインスタンス管理
_ephemeral_token_manager_instance: Optional[EphemeralTokenManager] = None


def get_ephemeral_token_manager(
    api_key: Optional[str] = None,
    force_new: bool = False
) -> EphemeralTokenManager:
    """
    EphemeralTokenManagerのシングルトンインスタンスを取得

    Args:
        api_key: Gemini API Key（Noneの場合は環境変数から取得）
        force_new: True の場合は新しいインスタンスを強制作成

    Returns:
        EphemeralTokenManager インスタンス

    Raises:
        ValueError: API Keyが設定されていない場合
    """
    global _ephemeral_token_manager_instance

    if force_new or _ephemeral_token_manager_instance is None:
        # API Key取得
        if api_key is None:
            api_key = os.getenv('GEMINI_API_KEY')

        if not api_key:
            raise ValueError("GEMINI_API_KEY環境変数が設定されていません")

        # インスタンス作成
        _ephemeral_token_manager_instance = EphemeralTokenManager(
            api_key=api_key,
            api_version=os.getenv('GEMINI_LIVE_API_VERSION', 'v1alpha'),
            expire_minutes=int(os.getenv('EPHEMERAL_TOKEN_EXPIRE_MINUTES', '30')),
            new_session_expire_minutes=int(os.getenv('EPHEMERAL_TOKEN_NEW_SESSION_EXPIRE_MINUTES', '1'))
        )

    return _ephemeral_token_manager_instance


# 便利関数
def create_ephemeral_token(model: Optional[str] = None) -> Dict[str, Any]:
    """
    Ephemeralトークンを簡単に生成する便利関数

    Args:
        model: モデル名（オプション）

    Returns:
        トークンデータ
    """
    manager = get_ephemeral_token_manager()
    return manager.create_token(model=model)
