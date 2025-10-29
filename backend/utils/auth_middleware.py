"""
JWT認証ミドルウェア
Supabase Auth JWTトークンを検証
"""
import os
import jwt
from functools import wraps
from flask import request, jsonify
from typing import Callable, Any
from utils.logger import setup_logger

logger = setup_logger(__name__)


def verify_jwt_token(token: str) -> dict:
    """
    Supabase JWTトークンを検証

    Args:
        token: JWTトークン（Bearer形式）

    Returns:
        dict: デコードされたペイロード（user_id, email等）

    Raises:
        jwt.InvalidTokenError: トークンが無効な場合
    """
    supabase_jwt_secret = os.getenv('SUPABASE_JWT_SECRET')
    if not supabase_jwt_secret:
        raise ValueError("SUPABASE_JWT_SECRET環境変数が設定されていません")

    try:
        # Bearerプレフィックスを削除
        if token.startswith('Bearer '):
            token = token[7:]

        # JWTトークンをデコード
        payload = jwt.decode(
            token,
            supabase_jwt_secret,
            algorithms=['HS256'],
            audience='authenticated'
        )

        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        raise
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise


def require_auth(f: Callable) -> Callable:
    """
    認証が必要なエンドポイント用デコレーター

    使用例:
        @app.route('/api/protected')
        @require_auth
        def protected_endpoint():
            user_id = request.user_id  # JWTから取得したuser_id
            return jsonify({'message': 'success'})
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            logger.warning("Missing Authorization header")
            return jsonify({'error': '認証が必要です'}), 401

        try:
            payload = verify_jwt_token(auth_header)

            # user_idをrequestオブジェクトに追加
            request.user_id = payload.get('sub')  # 'sub'がuser_id
            request.user_email = payload.get('email')
            request.user_role = payload.get('role', 'authenticated')

            logger.debug(f"Authenticated user: {request.user_id}")

            return f(*args, **kwargs)

        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'トークンの有効期限が切れています'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': '無効なトークンです'}), 401
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return jsonify({'error': '認証エラーが発生しました'}), 500

    return decorated_function


def optional_auth(f: Callable) -> Callable:
    """
    認証がオプションのエンドポイント用デコレーター
    認証情報があれば検証するが、なくてもエンドポイントにアクセス可能

    使用例:
        @app.route('/api/public')
        @optional_auth
        def public_endpoint():
            user_id = getattr(request, 'user_id', None)
            if user_id:
                # 認証済みユーザー向けの処理
            else:
                # 未認証ユーザー向けの処理
            return jsonify({'message': 'success'})
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        auth_header = request.headers.get('Authorization')

        if auth_header:
            try:
                payload = verify_jwt_token(auth_header)
                request.user_id = payload.get('sub')
                request.user_email = payload.get('email')
                request.user_role = payload.get('role', 'authenticated')
                logger.debug(f"Authenticated user: {request.user_id}")
            except Exception as e:
                logger.debug(f"Optional auth failed: {e}")
                # 認証失敗してもエンドポイントにアクセス可能

        return f(*args, **kwargs)

    return decorated_function
