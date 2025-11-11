"""
JWT認証ミドルウェア
Firebase Auth JWTトークンを検証
"""
import os
from functools import wraps
from flask import request, jsonify
from typing import Callable, Any
from utils.logger import setup_logger
from firebase_admin import auth as firebase_auth

logger = setup_logger(__name__)


def verify_jwt_token(token: str) -> dict:
    """
    Firebase JWTトークンを検証

    Args:
        token: JWTトークン（Bearer形式）

    Returns:
        dict: デコードされたペイロード（uid, email等）

    Raises:
        Exception: トークンが無効な場合
    """
    try:
        # Bearerプレフィックスを削除
        if token.startswith('Bearer '):
            token = token[7:]

        # Firebase Admin SDKでトークンを検証
        decoded_token = firebase_auth.verify_id_token(token)

        return decoded_token

    except firebase_auth.ExpiredIdTokenError:
        logger.warning("Firebase token has expired")
        raise
    except firebase_auth.InvalidIdTokenError as e:
        logger.warning(f"Invalid Firebase token: {e}")
        raise
    except Exception as e:
        logger.warning(f"Token verification error: {e}")
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
            request.user_id = payload.get('uid')  # Firebaseでは'uid'がuser_id
            request.user_email = payload.get('email')
            request.user_role = 'authenticated'

            logger.debug(f"Authenticated user: {request.user_id}")

            return f(*args, **kwargs)

        except firebase_auth.ExpiredIdTokenError:
            return jsonify({'error': 'トークンの有効期限が切れています'}), 401
        except firebase_auth.InvalidIdTokenError:
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

        logger.info(f"[optional_auth] Authorization header: {'あり (長さ: ' + str(len(auth_header)) + ')' if auth_header else 'なし'}")

        if auth_header:
            try:
                logger.info(f"[optional_auth] Firebase トークン検証中...")
                payload = verify_jwt_token(auth_header)
                request.user_id = payload.get('uid')  # Firebaseでは'uid'がuser_id
                request.user_email = payload.get('email')
                request.user_role = 'authenticated'
                logger.info(f"[optional_auth] ✅ 認証成功: user_id={request.user_id}, email={request.user_email}")
            except Exception as e:
                logger.warning(f"[optional_auth] ❌ 認証失敗: {type(e).__name__}: {str(e)}")
                # 認証失敗してもエンドポイントにアクセス可能
        else:
            logger.info(f"[optional_auth] Authorization ヘッダーなし - ゲストモード")

        return f(*args, **kwargs)

    return decorated_function
