"""共通設定モジュール"""
import os


def get_sessions_dir() -> str:
    """セッションディレクトリのパスを取得

    環境変数SESSIONS_DIRで上書き可能。
    - 絶対パス: そのまま使用
    - 相対パス: backend/ディレクトリ基準で解釈される

    デフォルト: backend/tmp/user_sessions

    Returns:
        str: セッションディレクトリの絶対パス

    Examples:
        # デフォルト
        get_sessions_dir()  # -> /path/to/backend/tmp/user_sessions

        # 環境変数で相対パス指定（backend/基準）
        SESSIONS_DIR=custom_sessions  # -> /path/to/backend/custom_sessions
        SESSIONS_DIR=tmp/custom      # -> /path/to/backend/tmp/custom

        # 環境変数で絶対パス指定
        SESSIONS_DIR=/var/app/sessions  # -> /var/app/sessions
    """
    # backend/ ディレクトリを取得（agents/ の親）
    backend_root = os.path.dirname(os.path.dirname(__file__))

    # 環境変数で上書き可能
    if env_dir := os.environ.get("SESSIONS_DIR"):
        # 絶対パスならそのまま、相対パスならbackend/基準で解決
        if os.path.isabs(env_dir):
            return env_dir
        else:
            return os.path.abspath(os.path.join(backend_root, env_dir))

    # デフォルト
    return os.path.join(backend_root, "tmp", "user_sessions")
