"""
環境変数検証モジュール
アプリケーション起動時に必要な環境変数をチェック
"""
import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class EnvVar:
    """環境変数定義"""
    name: str
    required: bool = True
    default: Optional[str] = None
    description: str = ""


class EnvValidationError(Exception):
    """環境変数検証エラー"""
    pass


class EnvValidator:
    """環境変数検証クラス"""

    # 必須環境変数の定義
    REQUIRED_VARS = [
        EnvVar(
            name="GEMINI_API_KEY",
            required=True,
            description="Gemini APIキー（https://aistudio.google.com/app/apikeyで取得）"
        ),
    ]

    # オプション環境変数の定義
    OPTIONAL_VARS = [
        EnvVar(
            name="FLASK_DEBUG",
            required=False,
            default="False",
            description="Flaskデバッグモード（True/False）"
        ),
        EnvVar(
            name="PORT",
            required=False,
            default="8080",
            description="APIサーバーのポート番号"
        ),
        EnvVar(
            name="LOG_LEVEL",
            required=False,
            default="INFO",
            description="ログレベル（DEBUG/INFO/WARNING/ERROR/CRITICAL）"
        ),
        EnvVar(
            name="SESSIONS_DIR",
            required=False,
            default="tmp/user_sessions",
            description="セッションデータの保存先ディレクトリ"
        ),
        EnvVar(
            name="ALLOWED_ORIGINS",
            required=False,
            default="http://localhost:3000",
            description="CORS許可オリジン（カンマ区切り）"
        ),
    ]

    @classmethod
    def validate(cls, raise_on_error: bool = True) -> Dict[str, Any]:
        """
        環境変数を検証

        Args:
            raise_on_error: エラー時に例外を発生させるかどうか

        Returns:
            Dict[str, Any]: 検証結果
                - valid: bool - 検証が成功したかどうか
                - missing: List[str] - 不足している必須環境変数のリスト
                - warnings: List[str] - 警告メッセージのリスト

        Raises:
            EnvValidationError: 必須環境変数が不足している場合（raise_on_error=Trueの時）
        """
        missing = []
        warnings = []

        # 必須環境変数のチェック
        for var in cls.REQUIRED_VARS:
            value = os.getenv(var.name)
            if not value:
                missing.append(var.name)

        # オプション環境変数のチェック（警告のみ）
        for var in cls.OPTIONAL_VARS:
            value = os.getenv(var.name)
            if not value and var.default:
                warnings.append(
                    f"{var.name}が設定されていません。デフォルト値「{var.default}」を使用します。"
                )

        result = {
            "valid": len(missing) == 0,
            "missing": missing,
            "warnings": warnings
        }

        if raise_on_error and not result["valid"]:
            error_message = cls._format_error_message(missing)
            raise EnvValidationError(error_message)

        return result

    @classmethod
    def _format_error_message(cls, missing: List[str]) -> str:
        """エラーメッセージをフォーマット"""
        lines = ["❌ 必須の環境変数が設定されていません:\n"]

        for var_name in missing:
            var = next((v for v in cls.REQUIRED_VARS if v.name == var_name), None)
            if var:
                lines.append(f"  • {var.name}")
                if var.description:
                    lines.append(f"    説明: {var.description}")

        lines.append("\n📝 .envファイルを作成して、上記の環境変数を設定してください。")
        lines.append("   例: backend/.env.exampleを参照")

        return "\n".join(lines)

    @classmethod
    def print_status(cls) -> None:
        """環境変数の状態を表示"""
        print("=" * 60)
        print("環境変数チェック")
        print("=" * 60)

        result = cls.validate(raise_on_error=False)

        if result["valid"]:
            print("✅ 必須環境変数: すべて設定済み")
        else:
            print(f"❌ 必須環境変数: {len(result['missing'])}件不足")
            for var_name in result["missing"]:
                print(f"   - {var_name}")

        if result["warnings"]:
            print(f"\n⚠️  警告: {len(result['warnings'])}件")
            for warning in result["warnings"]:
                print(f"   - {warning}")

        print("=" * 60)


def validate_env() -> None:
    """
    環境変数を検証（エントリーポイント）
    不足している場合は例外を発生させる
    """
    EnvValidator.validate(raise_on_error=True)


if __name__ == "__main__":
    # テスト実行
    EnvValidator.print_status()
