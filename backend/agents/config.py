"""共通設定モジュール"""
import os


def get_sessions_dir() -> str:
    """セッションディレクトリのパスを取得

    環境変数SESSIONS_DIRで上書き可能。
    デフォルトは backend/tmp/user_sessions

    Returns:
        str: セッションディレクトリの絶対パス
    """
    # 環境変数で上書き可能
    if env_dir := os.environ.get("SESSIONS_DIR"):
        return env_dir

    # backend/ ディレクトリを取得（agents/ の親）
    backend_root = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(backend_root, "tmp", "user_sessions")
