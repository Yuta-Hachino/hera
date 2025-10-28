"""
環境変数検証モジュールのテスト
"""
import os
import pytest
from utils.env_validator import EnvValidator, EnvValidationError


class TestEnvValidator:
    """EnvValidatorクラスのテスト"""

    def test_validate_with_all_required_vars(self, monkeypatch):
        """必須環境変数が全て設定されている場合"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-api-key')

        result = EnvValidator.validate(raise_on_error=False)

        assert result['valid'] is True
        assert len(result['missing']) == 0

    def test_validate_without_required_vars(self, monkeypatch):
        """必須環境変数が不足している場合"""
        monkeypatch.delenv('GEMINI_API_KEY', raising=False)

        result = EnvValidator.validate(raise_on_error=False)

        assert result['valid'] is False
        assert 'GEMINI_API_KEY' in result['missing']

    def test_validate_raises_error_when_missing(self, monkeypatch):
        """必須環境変数が不足している場合に例外を発生させる"""
        monkeypatch.delenv('GEMINI_API_KEY', raising=False)

        with pytest.raises(EnvValidationError) as exc_info:
            EnvValidator.validate(raise_on_error=True)

        assert 'GEMINI_API_KEY' in str(exc_info.value)

    def test_validate_with_optional_vars(self, monkeypatch):
        """オプション環境変数が設定されていない場合（警告のみ）"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-api-key')
        monkeypatch.delenv('FLASK_DEBUG', raising=False)

        result = EnvValidator.validate(raise_on_error=False)

        assert result['valid'] is True
        assert len(result['warnings']) > 0

    def test_format_error_message(self):
        """エラーメッセージのフォーマット"""
        missing = ['GEMINI_API_KEY']
        message = EnvValidator._format_error_message(missing)

        assert '❌' in message
        assert 'GEMINI_API_KEY' in message
        assert '.env' in message


@pytest.fixture(autouse=True)
def cleanup_env():
    """各テスト後に環境変数をクリーンアップ"""
    yield
    # テスト後の処理（必要に応じて）
