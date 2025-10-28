"""
ロギングモジュールのテスト
"""
import os
import logging
import pytest
import tempfile
from utils.logger import setup_logger, get_logger


class TestLogger:
    """ロガーのテスト"""

    def test_setup_logger_basic(self):
        """基本的なロガー設定"""
        logger = setup_logger('test_logger')

        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'test_logger'
        assert logger.level == logging.INFO

    def test_setup_logger_with_custom_level(self):
        """カスタムログレベルの設定"""
        logger = setup_logger('test_logger_debug', level='DEBUG')

        assert logger.level == logging.DEBUG

    def test_setup_logger_with_file(self):
        """ファイル出力付きロガーの設定"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = os.path.join(tmp_dir, 'test.log')
            logger = setup_logger('test_logger_file', log_file=log_file)

            # ログを出力
            logger.info('Test message')

            # ファイルが作成されたことを確認
            assert os.path.exists(log_file)

            # ファイルの内容を確認
            with open(log_file, 'r') as f:
                content = f.read()
                assert 'Test message' in content

    def test_get_logger_returns_existing(self):
        """既存のロガーを取得"""
        logger1 = setup_logger('test_get_logger')
        logger2 = get_logger('test_get_logger')

        assert logger1 is logger2

    def test_logger_env_level(self, monkeypatch):
        """環境変数からログレベルを設定"""
        monkeypatch.setenv('LOG_LEVEL', 'WARNING')

        logger = setup_logger('test_env_logger')

        assert logger.level == logging.WARNING

    def test_logger_console_handler(self):
        """コンソールハンドラが設定されている"""
        logger = setup_logger('test_console')

        handlers = logger.handlers
        assert len(handlers) >= 1
        assert any(isinstance(h, logging.StreamHandler) for h in handlers)

    def test_logger_file_handler(self):
        """ファイルハンドラが設定されている"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = os.path.join(tmp_dir, 'test.log')
            logger = setup_logger('test_file_handler', log_file=log_file)

            handlers = logger.handlers
            assert len(handlers) >= 2  # console + file
            assert any(isinstance(h, logging.Handler) for h in handlers)


@pytest.fixture(autouse=True)
def cleanup_loggers():
    """各テスト後にロガーをクリーンアップ"""
    yield
    # テスト後の処理
    logging.getLogger().handlers.clear()
