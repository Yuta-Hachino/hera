"""共通設定モジュール（Hera用）"""
import os


def get_sessions_dir() -> str:
    """セッションディレクトリのパスを取得

    環境変数SESSIONS_DIRで上書き可能。
    - 絶対パス: そのまま使用
    - 相対パス: backend/ディレクトリ基準で解釈される

    デフォルト: backend/tmp/user_sessions

    Returns:
        str: セッションディレクトリの絶対パス
    """
    # backend/ ディレクトリを取得（agents/hera の2つ上）
    backend_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    # 環境変数で上書き可能
    if env_dir := os.environ.get("SESSIONS_DIR"):
        # 絶対パスならそのまま、相対パスならbackend/基準で解決
        if os.path.isabs(env_dir):
            return env_dir
        else:
            return os.path.abspath(os.path.join(backend_root, env_dir))

    # デフォルト
    return os.path.join(backend_root, "tmp", "user_sessions")
