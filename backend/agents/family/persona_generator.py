"""LLMベースのペルソナ生成モジュール"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List

import google.generativeai as genai
from google.generativeai import GenerativeModel

from .models import Persona

logger = logging.getLogger(__name__)


class PersonaGenerator:
    """ユーザープロファイルからLLMで家族ペルソナを生成"""

    def __init__(self, model_name: str = "gemini-2.5-pro"):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY または GEMINI_API_KEY が設定されていません")
        genai.configure(api_key=api_key)
        self.model = GenerativeModel(model_name)

    async def generate_personas(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """ユーザープロファイルから家族全員のペルソナを一括生成

        Args:
            user_profile: Heraエージェントが収集したユーザー情報

        Returns:
            Dict containing:
                - partner: パートナーのペルソナ情報
                - children: 子供たちのペルソナ情報リスト

        Example:
            {
                "partner": {
                    "name": "未来の妻",
                    "role": "妻",
                    "speaking_style": "優しく穏やかな口調",
                    "traits": ["思いやりがある", "協調性が高い"],
                    "goals": "家族みんなで幸せな時間を過ごすこと",
                    "background": "30代の主婦。家族との時間を大切にしている。"
                },
                "children": [
                    {
                        "name": "未来の娘",
                        "role": "娘",
                        ...
                    }
                ]
            }
        """
        prompt = self._build_prompt(user_profile)

        try:
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.model.generate_content, prompt)
            text = response.text if hasattr(response, "text") else str(response)

            # JSONの前後のマークダウンコードブロックを除去
            text_cleaned = text.strip()
            if text_cleaned.startswith("```json"):
                text_cleaned = text_cleaned[7:]
            if text_cleaned.startswith("```"):
                text_cleaned = text_cleaned[3:]
            if text_cleaned.endswith("```"):
                text_cleaned = text_cleaned[:-3]
            text_cleaned = text_cleaned.strip()

            result = json.loads(text_cleaned)
            logger.info(f"ペルソナ生成完了: パートナー1名, 子供{len(result.get('children', []))}名")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"LLM応答のJSON解析に失敗しました: {e}")
            logger.error(f"応答テキスト: {text[:500]}")
            raise ValueError(f"ペルソナ生成に失敗しました: JSON解析エラー") from e
        except Exception as e:
            logger.error(f"ペルソナ生成中にエラーが発生しました: {e}", exc_info=True)
            raise

    def _build_prompt(self, profile: Dict[str, Any]) -> str:
        """ペルソナ生成用のプロンプトを構築"""

        # プロファイルから主要情報を抽出
        relationship_status = profile.get("relationship_status", "single")

        # パートナー情報の取得（状況に応じて分岐）
        if relationship_status in ["married", "partnered"]:
            partner_info = profile.get("current_partner", {})
            partner_context = "既婚/交際中のため、現在のパートナーの情報を基にペルソナを生成してください。"
        else:
            partner_info = profile.get("ideal_partner", {})
            partner_context = "独身のため、理想のパートナー像を基にペルソナを生成してください。"

        children_info = profile.get("children_info", [])
        user_traits = profile.get("user_personality_traits", {})
        partner_face_desc = profile.get("partner_face_description", "")
        lifestyle = profile.get("lifestyle", {})
        age = profile.get("age")

        # プロファイル情報をJSON形式で整形
        profile_json = json.dumps({
            "relationship_status": relationship_status,
            "partner_info": partner_info,
            "children_info": children_info,
            "user_personality_traits": user_traits,
            "partner_face_description": partner_face_desc,
            "lifestyle": lifestyle,
            "age": age
        }, ensure_ascii=False, indent=2)

        return f"""あなたは家族シミュレーションのためのペルソナ（AIエージェントの人格設定）を生成する専門家です。

以下のユーザープロファイルを基に、未来の家族メンバー（パートナーと子供たち）のペルソナを生成してください。

# ユーザープロファイル
```json
{profile_json}
```

# 注意事項
{partner_context}

# 出力形式
以下のJSON形式で出力してください。JSON以外のテキストは一切含めないでください。

```json
{{
  "partner": {{
    "name": "パートナーの名前（例: 未来の妻、未来の夫）",
    "role": "役割（例: 妻、夫、パートナー）",
    "speaking_style": "話し方の特徴（例: 優しく穏やかな口調、明るく元気な話し方）",
    "traits": ["性格特性1", "性格特性2", "性格特性3"],
    "goals": "家族に対する願いや目標",
    "background": "背景情報や人物像の簡単な説明"
  }},
  "children": [
    {{
      "name": "子供の名前（例: 未来の娘、未来の息子）",
      "role": "役割（例: 娘、息子、長男、次女）",
      "speaking_style": "話し方の特徴（年齢に応じた話し方）",
      "traits": ["性格特性1", "性格特性2", "性格特性3"],
      "goals": "子供らしい願いや目標",
      "background": "年齢や性格、興味のある事柄"
    }}
  ]
}}
```

# ペルソナ生成のガイドライン

## パートナー
- プロファイルの personality_traits（ビッグファイブ）から性格特性を推測
- partner_face_description があれば外見的な特徴も考慮
- lifestyle の future_hope があれば goals に反映
- speaking_style は性格特性と一致するように設定
- traits は3-5個程度、具体的で分かりやすい日本語で

## 子供
- children_info の情報（性別、希望する人数など）を考慮
- 親の personality_traits を参考に、遺伝的・環境的影響を考慮した性格を設定
- 年齢は明示されていない場合、5-12歳程度の子供を想定
- speaking_style は子供らしい表現に
- traits は子供らしい特性を含める（例: 好奇心旺盛、元気いっぱい）
- 複数の子供がいる場合、それぞれ個性を持たせる

## 重要な注意点
- 全て日本語で生成してください
- 家族シミュレーションのため、温かみのある設定にしてください
- 各メンバーの個性が明確に分かれるように設定してください
- JSON形式を厳守してください（マークダウンのコードブロックは除く）

それでは、上記のプロファイルを基にペルソナを生成してください。"""

    def build_persona_objects(self, generated_data: Dict[str, Any]) -> List[Persona]:
        """生成されたJSON データからPersonaオブジェクトのリストを構築

        Args:
            generated_data: generate_personas() の返り値

        Returns:
            List[Persona]: パートナーと子供を含む全ペルソナのリスト
        """
        personas = []

        # パートナー（必須）
        partner_data = generated_data.get("partner", {})
        if partner_data and (partner_data.get("name") or partner_data.get("role")):
            personas.append(Persona(
                name=partner_data.get("name", "未来のパートナー"),
                role=partner_data.get("role", "パートナー"),
                speaking_style=partner_data.get("speaking_style", "優しい口調"),
                traits=partner_data.get("traits", []),
                goals=partner_data.get("goals", "家族の幸せ"),
                background=partner_data.get("background", ""),
                history=[]
            ))
        else:
            logger.warning("パートナーのペルソナデータが不足しています")

        # 子供たち
        children_data = generated_data.get("children", [])
        for child_data in children_data:
            personas.append(Persona(
                name=child_data.get("name", "未来の子供"),
                role=child_data.get("role", "子供"),
                speaking_style=child_data.get("speaking_style", "元気な話し方"),
                traits=child_data.get("traits", []),
                goals=child_data.get("goals", "楽しく過ごす"),
                background=child_data.get("background", ""),
                history=[]
            ))

        return personas
