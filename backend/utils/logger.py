"""
ロギング設定モジュール
アプリケーション全体で統一されたロギングを提供
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logger(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    ロガーをセットアップ

    Args:
        name: ロガー名（通常は__name__を使用）
        level: ログレベル（環境変数LOG_LEVELで上書き可能）
        log_file: ログファイルのパス（指定時のみファイル出力）
        max_bytes: ログファイルの最大サイズ（バイト）
        backup_count: ログファイルのバックアップ数

    Returns:
        logging.Logger: 設定済みロガー
    """
    logger = logging.getLogger(name)

    # 既にハンドラが設定されている場合はスキップ
    if logger.handlers:
        return logger

    # ログレベルの設定
    log_level = (
        level or
        os.getenv('LOG_LEVEL', 'INFO')
    ).upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # フォーマッター
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # コンソールハンドラ
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイルハンドラ（log_file指定時のみ）
    if log_file:
        # ログディレクトリの作成
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # 上位ロガーへの伝播を防止（重複ログ防止）
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    既存のロガーを取得、または新規作成

    Args:
        name: ロガー名

    Returns:
        logging.Logger: ロガー
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
