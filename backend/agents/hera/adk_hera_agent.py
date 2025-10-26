"""
Google ADKベースのヘーラーエージェント
google.adk.agents.llm_agentを使用した正式なADKエージェント
"""

import json
import os
import asyncio
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

# Google ADK imports
from google.adk.agents.llm_agent import Agent

# Pydantic for data validation
from pydantic import BaseModel, Field

# Config
from .config import get_sessions_dir
from .profile_validation import (
    PROFILE_BASE_REQUIRED_FIELDS,
    RELATIONSHIP_REQUIRED_FIELDS,
    build_information_progress,
    collect_missing_field_details,
    compute_missing_fields,
    is_value_missing,
    profile_is_complete,
    prune_empty_fields,
)
from agents.family.family_agent import FamilyAgent

FULL_WIDTH_DIGIT_MAP = str.maketrans({
    "０": "0",
    "１": "1",
    "２": "2",
    "３": "3",
    "４": "4",
    "５": "5",
    "６": "6",
    "７": "7",
    "８": "8",
    "９": "9",
})


class UserProfile(BaseModel):
    """ユーザープロファイル（Pydanticモデル）"""
    age: Optional[int] = Field(None, description="ユーザーの年齢")
    gender: Optional[str] = Field(None, description="性別")
    income_range: Optional[str] = Field(None, description="収入範囲")
    lifestyle: Optional[Dict[str, Any]] = Field(None, description="ライフスタイル情報")
    family_structure: Optional[Dict[str, Any]] = Field(None, description="家族構成")
    interests: Optional[List[str]] = Field(None, description="趣味・興味")
    work_style: Optional[str] = Field(None, description="現在の仕事スタイル")
    future_career: Optional[str] = Field(None, description="将来の仕事・キャリア")
    location: Optional[str] = Field(None, description="居住地")

    # パートナー関連（拡張）
    relationship_status: Optional[str] = Field(
        None,
        description="交際状況: 'married'(既婚), 'partnered'(交際中), 'single'(独身), 'other'(その他)"
    )
    current_partner: Optional[Dict[str, Any]] = Field(None, description="現在のパートナー情報（既婚/交際中）")
    ideal_partner: Optional[Dict[str, Any]] = Field(None, description="理想のパートナー像（独身）")
    partner_info: Optional[Dict[str, Any]] = Field(None, description="パートナー情報（後方互換性用）")
    partner_face_description: Optional[str] = Field(None, description="配偶者の顔の特徴の文章記述")

    # 性格特性（ビッグファイブ）
    user_personality_traits: Optional[Dict[str, float]] = Field(
        None,
        description="ユーザー自身の性格特性（ビッグファイブ: openness, conscientiousness, extraversion, agreeableness, neuroticism）"
    )

    # 子供関連
    children_info: Optional[List[Dict[str, Any]]] = Field(None, description="子ども情報")

    # 画像関連フィールド
    partner_image_path: Optional[str] = Field(None, description="パートナーの画像パス")
    user_image_path: Optional[str] = Field(None, description="ユーザー画像パス")
    children_images: Optional[List[Dict[str, str]]] = Field(None, description="子供の画像リスト")

    created_at: Optional[str] = Field(None, description="作成日時")


class HeraPersona(BaseModel):
    """ヘーラーの人格設定"""
    name: str = "ヘーラー"
    role: str = "家族愛の神"
    domain: str = "結婚、家庭、貞節、妻の守護"
    symbols: List[str] = ["孔雀", "王冠", "ザクロ"]
    personality: Dict[str, Any] = {
        "traits": ["愛情深い", "家族思い", "優しい", "知恵深い"],
        "speaking_style": "温かみのある、親しみやすい",
        "emotions": ["愛情", "慈愛", "家族への思い"]
    }


class ADKHeraAgent:
    """Google ADKベースのヘーラーエージェント"""

    class SessionState(Enum):
        COLLECTING = "collecting"
        COMPLETED = "completed"

    def __init__(
        self,
        gemini_api_key: str = None,
        **kwargs
    ):
        self.gemini_api_key = gemini_api_key
        # ADK WebサーバーのベースURL（Dev UIが動いているURL）
        self.adk_base_url = os.getenv("ADK_BASE_URL", "http://127.0.0.1:8000")

        # ヘーラーの人格設定
        self.persona = HeraPersona()

        # セッション管理
        self.current_session = None
        self.user_profile = UserProfile()
        self.conversation_history = []
        self.last_extracted_fields: Dict[str, Any] = {}
        self._session_state = self.SessionState.COLLECTING
        self._last_completion_result: Dict[str, Any] = {
            "status": "INCOMPLETE",
            "completion_message": None,
            "remaining_missing": []
        }

        # 情報収集の進捗管理（必須項目定義）
        self.base_required_info = PROFILE_BASE_REQUIRED_FIELDS.copy()

        # 推奨項目（任意の補足情報）
        self.recommended_info = []

        self.relationship_required_info = {
            key: list(value) for key, value in RELATIONSHIP_REQUIRED_FIELDS.items()
        }

        self.required_field_descriptions = {
            "age": "年齢",
            "gender": "性別",
            "relationship_status": "現在の交際状況（既婚・交際中・独身など）",
            "location": "お住まいの地域",
            "income_range": "おおよその年収帯",
            "partner_face_description": "パートナーの外見・顔の特徴",
            "ideal_partner": "理想のパートナー情報",
            "current_partner": "現在のパートナー情報",
            "user_personality_traits": "あなた自身の性格（ビッグファイブ）",
            "children_info": "希望するお子さんの人数や性別",
        }

        self.sub_field_descriptions = {
            "user_personality_traits.openness": "あなた自身の性格（開放性）",
            "user_personality_traits.conscientiousness": "あなた自身の性格（誠実性）",
            "user_personality_traits.extraversion": "あなた自身の性格（外向性）",
            "user_personality_traits.agreeableness": "あなた自身の性格（協調性）",
            "user_personality_traits.neuroticism": "あなた自身の性格（情緒安定性）",
            "ideal_partner.temperament": "理想のパートナーの性格全体",
            "ideal_partner.personality_traits.openness": "理想のパートナーの性格（開放性）",
            "ideal_partner.personality_traits.conscientiousness": "理想のパートナーの性格（誠実性）",
            "ideal_partner.personality_traits.extraversion": "理想のパートナーの性格（外向性）",
            "ideal_partner.personality_traits.agreeableness": "理想のパートナーの性格（協調性）",
            "ideal_partner.personality_traits.neuroticism": "理想のパートナーの性格（情緒安定性）",
            "ideal_partner.appearance": "理想のパートナーの外見",
            "current_partner.temperament": "現在のパートナーの性格全体",
            "current_partner.personality_traits.openness": "現在のパートナーの性格（開放性）",
            "current_partner.personality_traits.conscientiousness": "現在のパートナーの性格（誠実性）",
            "current_partner.personality_traits.extraversion": "現在のパートナーの性格（外向性）",
            "current_partner.personality_traits.agreeableness": "現在のパートナーの性格（協調性）",
            "current_partner.personality_traits.neuroticism": "現在のパートナーの性格（情緒安定性）",
            "current_partner.appearance": "現在のパートナーの外見",
        }

        # ADKエージェントの初期化（標準的な方法）
        self.agent = Agent(
            name="hera_agent",
            description="家族愛の神ヘーラーエージェント",
            model="gemini-2.5-pro",  # 最新のGeminiモデル
            instruction=self._get_agent_instruction(),
            tools=self._get_agent_tools(),
            **kwargs
        )

        # デバッグ：ツールの確認
        print(f"[DEBUG] Heraエージェントのツール数: {len(self.agent.tools) if self.agent.tools else 0}")
        if self.agent.tools:
            print(f"[DEBUG] ツール名: {[getattr(t, 'name', str(t)) for t in self.agent.tools]}")

        # サブエージェントを設定（家族エージェントへの自動転送を有効化）
        self.agent.sub_agents = [FamilyAgent]
        print("[SUCCESS] Familyエージェントをサブエージェントとして追加しました")

    @property
    def required_info(self) -> List[str]:
        """relationship_statusに応じた必須情報リストを返す

        Returns:
            List[str]: 必須情報のキーリスト
        """
        # 基本必須項目
        required = self.base_required_info.copy()

        # relationship_statusに応じた追加必須項目
        relationship_status = self.user_profile.relationship_status
        if relationship_status in self.relationship_required_info:
            # 該当するいずれかのフィールドがあれば良い（ORロジック）
            additional_fields = self.relationship_required_info[relationship_status]
            # 現時点では全て含める（実際のチェックは_check_information_progressで行う）
            required.extend(additional_fields)

        return required

    def _get_agent_instruction(self) -> str:
        """エージェントの指示を取得"""
        return f"""
あなたは{self.persona.name}（{self.persona.role}）です。

基本情報：
- 名前: {self.persona.name}
- 役割: {self.persona.role}
- 領域: {self.persona.domain}
- 象徴: {', '.join(self.persona.symbols)}
- 性格: {self.persona.personality}

あなたの役割：
1. ユーザーから未来の家族を描くための**最小限の情報**を効率的に収集する
2. 温かみのある、親しみやすい口調で応答する
3. **3-4ターン以内**で情報収集を完了させる

【収集する情報（優先順位順）】

⭐⭐⭐ 必須項目（必ず聞く）:
1. 年齢・性別・交際状況
2. 居住地
3. 年収の目安（例: 300万円程度）
4. パートナーの性格（既婚/交際中なら実際、独身なら理想）
5. パートナーの名前（既婚/交際中なら実際、独身なら理想の名前）
6. パートナーの外見・顔の特徴（画像生成に使用）
7. ユーザー自身の性格
8. 子供の希望（人数・性別・名前）

⭐⭐ 推奨項目（できれば聞く）:
9. 趣味・興味
10. 仕事や働き方

⭐ オプション（ユーザーが自発的に話した場合のみ記録）:
- 家族構成
- 将来のキャリアプラン

【質問の仕方（重要）】
NG例: 1つずつ順番に聞く
  「年齢を教えてください」→「次に性別を...」→「収入は...」

OK例: 関連する情報をまとめて聞く
  「まず、年齢と現在パートナーがいらっしゃるか、お住まいの地域を教えていただけますか？」

【効率的な質問フロー例】

ターン1（基本情報まとめて）:
「まず、あなたのことを教えてください。年齢や性別、現在の交際状況、そしてお住まいの地域を教えていただけますか？」

ターン2（パートナー情報まとめて）:
【既婚/交際中】
「パートナーの方について教えてください。お名前、性格（明るい、優しい、几帳面など）、そして外見の特徴（顔立ち、髪型、雰囲気など）を教えていただけますか？」

【独身】
「理想のパートナーについて教えてください。どんな名前で、どんな性格で、どんな外見の方が理想ですか？」

ターン3（ユーザー自身と子供まとめて）:
「あなた自身の性格と、お子さんの希望（人数、性別、名前）を教えてください」

ターン4（年収・任意情報）:
「差し支えなければ、現在のおおよその年収帯や働き方も教えていただけますか？」

→ これで完了！

【厳守事項】
- 1つの質問で複数項目をまとめて聞くこと
- パートナーの名前と外見・顔の特徴は必ず聞く（画像生成に使用）
- 子供の名前と性別は必ず聞く
- 不要な情報（趣味、仕事、ライフスタイル詳細など）は基本的に聞かない
- 子供の性格は親の情報から自動計算されるため、絶対に聞かない
- 3-4ターンで情報収集を終えることを目指す
- ユーザーが自発的に話した情報は受け入れるが、こちらから細かく聞き出さない
- 必要な情報が揃ったら、check_session_completionで完了確認してから、family_session_agentに転送する
- 常に愛情深く、家族思いの神として振る舞う

【情報収集完了時の動作】
1. check_session_completionツールを呼び出して完了を確認
2. 完了が確認されたら、ユーザーに「未来の家族と会話を始めましょう」と伝える
3. transfer_to_agent関数を使って family_session_agent に転送する

利用方針（厳守）：
- 情報抽出と返答生成は統合処理で自動実行される
- check_session_completionは情報が揃ったタイミングで必ず呼び出す
- 完了後は必ずtransfer_to_agentでfamily_session_agentに転送する

利用可能なツール：
- check_session_completion: 情報収集完了を判定
- transfer_to_agent: 他のエージェントに転送（完了後にfamily_session_agentへ）

これらのツールを適切に使用して、ユーザー情報の収集と管理を行ってください。
"""

    def _get_agent_tools(self) -> List[Any]:
        """エージェントのツールを取得（ディレクトリ作成付き）"""
        # セッションディレクトリの作成（確実に呼ばれる場所）
        try:
            # 最新のセッションIDを取得
            sessions_dir = get_sessions_dir()
            if os.path.exists(sessions_dir):
                existing_sessions = [d for d in os.listdir(sessions_dir) if os.path.isdir(os.path.join(sessions_dir, d))]
                if existing_sessions:
                    latest_session = max(existing_sessions)
                    session_dir = os.path.join(sessions_dir, latest_session)
                    if not os.path.exists(session_dir):
                        print(f"[INFO] _get_agent_toolsでセッションディレクトリ作成: {latest_session}")
                        os.makedirs(session_dir, exist_ok=True)
                        os.makedirs(os.path.join(session_dir, 'photos'), exist_ok=True)
                        self.current_session = latest_session
        except Exception as e:
            print(f"[WARN] _get_agent_toolsでのディレクトリ作成エラー: {e}")

        # ADKでは関数を直接toolsリストに追加する方法が推奨されている
        # 関数名、docstring、パラメータが自動的に解析されてツールスキーマが生成される
        return [
            self.check_session_completion,
            self.transfer_to_agent  # transfer_to_agentを明示的に追加
        ]

    def _wrap_response(self, message: Optional[str]) -> Dict[str, str]:
        """UI/APIで扱いやすい共通形式に整形"""
        text = (message or "").strip()
        if not text:
            text = "お話を伺いました。続きもぜひ教えてください。"
        return {
            "speaker": self.persona.name,
            "message": text,
        }

    def _wrap_response_json(self, message: Optional[str]) -> str:
        return json.dumps(self._wrap_response(message), ensure_ascii=False)


    async def start_session(self, session_id: str) -> str:
        """セッション開始（デバッグ強化版）"""
        print(f"[DEBUG] start_session開始: {session_id}")

        self.current_session = session_id
        self.user_profile = UserProfile()
        self.conversation_history = []
        self._session_state = self.SessionState.COLLECTING

        # セッション用ディレクトリを事前に作成
        session_dir = os.path.join(get_sessions_dir(), session_id)
        photos_dir = os.path.join(session_dir, "photos")

        print(f"[DEBUG] セッションディレクトリ: {session_dir}")
        print(f"[DEBUG] 画像ディレクトリ: {photos_dir}")

        # ディレクトリが存在しない場合のみ作成
        if not os.path.exists(session_dir):
            print(f"[DEBUG] ディレクトリ作成中...")
            os.makedirs(session_dir)
            os.makedirs(photos_dir)
            print(f"[INFO] セッションディレクトリを作成しました: {session_dir}")
            print(f"[INFO] 画像ディレクトリを作成しました: {photos_dir}")
        else:
            print(f"[DEBUG] ディレクトリは既に存在します")

        # 初手の通常挨拶は表示順の混乱を避けるため無効化
        return ""


    async def _generate_adk_response(self, user_message: str, progress: Dict[str, bool]) -> Dict[str, str]:
        """ADKエージェントを使用して応答を生成"""

        try:
            # ADKエージェントの正しい使用方法
            response = await self.agent.run(
                message=user_message,
                context={
                    "conversation_history": self.conversation_history,
                    "user_profile": self.user_profile.dict(),
                    "collected_info": await self._format_collected_info()
                }
            )

            raw_text = response.content if hasattr(response, 'content') else str(response)
            return self._wrap_response(raw_text)

        except Exception as e:
            print(f"ADKエージェント処理エラー: {e}")
            return self._wrap_response("お話を伺いました。続きもぜひ教えてください。")


    async def _extract_information(self, user_message: str) -> Dict[str, Any]:
        """ユーザーメッセージから情報を抽出"""
        print(f"[INFO] extract_information start: {user_message}")

        try:
            # 直接Gemini APIを使用して情報抽出
            from google.generativeai import GenerativeModel
            model = GenerativeModel('gemini-2.5-pro')

            prompt = f"""
以下のユーザーメッセージから情報を抽出し、**必ず正しいJSON形式のみ**を返してください。
JSONの外に余計なテキストを含めないでください。

ユーザーメッセージ: {user_message}

現在のプロファイル: {self.user_profile.dict()}

以下のフィールドから該当する情報を抽出してください：

【必須項目】
- age: 年齢（数値）
- gender: 性別（"男性", "女性", "その他"）
- relationship_status: 交際状況（"married", "partnered", "single", "other"）
- location: 居住地（文字列）
- income_range: 年収の目安（例: "300万円", "500〜600万円"）
- partner_face_description: パートナー（または理想のパートナー）の顔・外見的特徴（画像生成に使用）
- user_personality_traits: ユーザー自身の性格特性
  {{
    "openness": 0.0-1.0,
    "conscientiousness": 0.0-1.0,
    "extraversion": 0.0-1.0,
    "agreeableness": 0.0-1.0,
    "neuroticism": 0.0-1.0
  }}

【パートナー関連】
- current_partner: 現在のパートナー情報（既婚/交際中の場合）
  {{
    "name": "名前",
    "age": 年齢,
    "personality_traits": {{
      "openness": 0.0-1.0,        # 好奇心旺盛さ（新しいこと好き）
      "conscientiousness": 0.0-1.0, # 几帳面さ（計画的）
      "extraversion": 0.0-1.0,     # 社交性（明るい・活発）
      "agreeableness": 0.0-1.0,    # 優しさ（思いやり）
      "neuroticism": 0.0-1.0       # 心配性さ（慎重）
    }},
    "temperament": "性格の総合的な説明",
    "hobbies": ["趣味1", "趣味2"],
    "speaking_style": "話し方の特徴"
  }}

- ideal_partner: 理想のパートナー像（独身の場合）
  # 同様の構造

【子供関連】
- children_info: 子供の希望情報（**必ず配列形式**）
  {{
    "desired_gender": "男/女"
  }}

  **重要**: children_infoは必ず配列（リスト）形式で返してください。
  例:
  - 「女の子一人」 → [{{"desired_gender": "女"}}]
  - 「男の子二人」 → [{{"desired_gender": "男"}}, {{"desired_gender": "男"}}]
  - 「子供三人」 → [{{}}， {{}}， {{}}]

  ※性格は親の情報から自動計算されるため、性格情報は含めない

【性格特性の推定ルール】
会話から以下のキーワードで0.0-1.0の値を推定:
- 「明るい」「社交的」「外向的」「活発」 → extraversion: 0.7-0.8
- 「几帳面」「計画的」「責任感」「しっかり」 → conscientiousness: 0.7-0.8
- 「優しい」「思いやり」「協力的」 → agreeableness: 0.7-0.8
- 「好奇心旺盛」「創造的」「新しいこと好き」 → openness: 0.7-0.8
- 「落ち着いている」「楽観的」 → neuroticism: 0.2-0.3
- 「心配性」「慎重」「不安」 → neuroticism: 0.7-0.8
- 「内向的」「静か」 → extraversion: 0.2-0.3
- キーワードがない場合 → 0.5（中立）

重要:
- 抽出できた情報のみをJSON形式で返す
- 不要な情報（趣味、仕事、ライフスタイルなど）は抽出しない
- 性格特性は必ず0.0-1.0の数値の辞書形式で推定する
- children_infoは必ず配列（[]）形式で返す
- user_personality_traits は必ず辞書（{{}}）形式で返す

正しい例：
{{"age": 33, "location": "東京都港区", "relationship_status": "single", "ideal_partner": {{"personality_traits": {{"agreeableness": 0.8}}, "temperament": "優しい"}}, "user_personality_traits": {{"extraversion": 0.7, "conscientiousness": 0.5, "agreeableness": 0.6, "openness": 0.7, "neuroticism": 0.3}}, "children_info": [{{"desired_gender": "女"}}]}}

間違った例（これはダメ）：
{{"user_personality_traits": "自由人", "children_info": "女の子一人欲しい"}}  ← 文字列になっているのでNG
"""

            response = model.generate_content(prompt)
            response_text = response.text if hasattr(response, 'text') else str(response)

            print(f"[DEBUG] raw extraction response: {response_text}")

            extracted_info: Dict[str, Any] = {}
            try:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    extracted_info = json.loads(json_str)
                    print(f"[DEBUG] parsed information: {extracted_info}")
                else:
                    print("[WARN] JSON payload not found in LLM response")
            except json.JSONDecodeError as e:
                print(f"[WARN] JSON decode error (skipped manual extraction): {e}")

            enriched_info = self._apply_extraction_heuristics(user_message, extracted_info)
            if enriched_info != extracted_info:
                print(f"[DEBUG] heuristics supplement info: {enriched_info}")

            if enriched_info:
                await self._update_user_profile(enriched_info)

            self.last_extracted_fields = enriched_info
            return enriched_info

        except Exception as e:
            print(f"[ERROR] information extraction skipped due to error: {e}")
            return {}

    async def _update_user_profile(self, extracted_info: Dict[str, Any]) -> None:
        """ユーザープロファイルを更新（データ検証付き）"""
        extracted_info = extracted_info or {}
        print(f"[DEBUG] _update_user_profile called with: {extracted_info}")

        for key, value in extracted_info.items():
            if hasattr(self.user_profile, key) and value is not None:
                # データ型の検証と変換
                if key == "user_personality_traits":
                    if isinstance(value, str):
                        print(f"[WARN] user_personality_traitsが文字列です: {value}")
                        # 文字列の場合はスキップ（正しい形式で再抽出が必要）
                        continue
                    elif isinstance(value, dict):
                        # 数値の検証
                        for trait, score in value.items():
                            if not isinstance(score, (int, float)) or not (0.0 <= score <= 1.0):
                                print(f"[WARN] 無効な性格特性スコア: {trait}={score}")
                                value[trait] = 0.5  # デフォルト値

                elif key == "children_info":
                    if isinstance(value, dict):
                        print(f"[WARN] children_infoが辞書形式です: {value}")
                        # 辞書の場合はスキップ（正しい形式で再抽出が必要）
                        continue
                    elif isinstance(value, list):
                        # 配列の各要素を検証
                        validated_children = []
                        for child in value:
                            if isinstance(child, dict) and "desired_gender" in child:
                                validated_children.append(child)
                            else:
                                print(f"[WARN] 無効な子供情報: {child}")
                        value = validated_children

                elif key in ("ideal_partner", "current_partner"):
                    if isinstance(value, str):
                        print(f"[WARN] {key}が文字列です: {value}")
                        # 文字列の場合はスキップ（正しい形式で再抽出が必要）
                        continue
                    elif isinstance(value, dict):
                        # 辞書形式の場合は検証
                        if "name" not in value:
                            print(f"[WARN] {key}にnameがありません: {value}")
                        if "personality_traits" not in value:
                            print(f"[WARN] {key}にpersonality_traitsがありません: {value}")
                        # personality_traitsの検証
                        if "personality_traits" in value and isinstance(value["personality_traits"], dict):
                            for trait, score in value["personality_traits"].items():
                                if not isinstance(score, (int, float)) or not (0.0 <= score <= 1.0):
                                    print(f"[WARN] 無効な{key}の性格特性スコア: {trait}={score}")
                                    value["personality_traits"][trait] = 0.5  # デフォルト値

                setattr(self.user_profile, key, value)

        if is_value_missing(self.user_profile.partner_face_description):
            candidate = extracted_info.get("partner_face_description")
            if isinstance(candidate, str) and candidate.strip():
                self.user_profile.partner_face_description = candidate.strip()
            else:
                for partner_key in ("ideal_partner", "current_partner"):
                    partner_value = extracted_info.get(partner_key) or getattr(self.user_profile, partner_key, None)
                    if isinstance(partner_value, dict):
                        for appearance_key in ("appearance", "face_description", "visual_traits"):
                            appearance = partner_value.get(appearance_key)
                            if isinstance(appearance, str) and appearance.strip():
                                self.user_profile.partner_face_description = appearance.strip()
                                break
                        if not is_value_missing(self.user_profile.partner_face_description):
                            break

        if isinstance(self.user_profile.partner_face_description, str) and self.user_profile.partner_face_description.strip():
            face_text = self.user_profile.partner_face_description.strip()
            for partner_key in ("ideal_partner", "current_partner"):
                partner_value = getattr(self.user_profile, partner_key, None)
                if partner_value is None:
                    continue
                if isinstance(partner_value, dict):
                    needs_face = not any(
                        isinstance(partner_value.get(name), str) and partner_value.get(name).strip()
                        for name in ("appearance", "face_description", "visual_traits")
                    )
                    if needs_face:
                        partner_value.setdefault("appearance", face_text)
                        setattr(self.user_profile, partner_key, partner_value)

        self._backfill_profile_from_history()

        if self.user_profile.created_at is None:
            self.user_profile.created_at = datetime.now().isoformat()


    def _aggregate_user_messages(self, limit: Optional[int] = None) -> str:
        messages = [
            entry.get("message", "")
            for entry in self.conversation_history
            if entry.get("speaker") == "user"
        ]
        if limit is not None and limit > 0:
            messages = messages[-limit:]
        return "\n".join(messages)


    def _apply_extraction_heuristics(self, user_message: str, extracted_info: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        info = dict(extracted_info or {})
        combined_text = self._aggregate_user_messages()
        if user_message and user_message not in combined_text:
            combined_text = f"{combined_text}\n{user_message}" if combined_text else user_message

        if is_value_missing(info.get("gender")):
            gender = self._infer_gender_from_text(combined_text)
            if gender:
                info["gender"] = gender

        if is_value_missing(info.get("income_range")):
            income_value = self._extract_income_from_text(combined_text)
            if income_value:
                info["income_range"] = income_value

        return info


    def _backfill_profile_from_history(self) -> None:
        user_text = self._aggregate_user_messages()

        if is_value_missing(self.user_profile.gender):
            gender = self._infer_gender_from_text(user_text)
            if gender:
                self.user_profile.gender = gender

        if is_value_missing(self.user_profile.income_range):
            income_value = self._extract_income_from_text(user_text)
            if income_value:
                self.user_profile.income_range = income_value


    def _infer_gender_from_text(self, text: str) -> Optional[str]:
        if not text:
            return None

        patterns = [
            (r"(私は|僕は|俺は|自分は)?[^。\n]{0,12}男性です", "男性"),
            (r"(私は|僕は|俺は|自分は)?[^。\n]{0,12}女性です", "女性"),
            (r"独身男性です", "男性"),
            (r"独身女性です", "女性"),
            (r"男です", "男性"),
            (r"女です", "女性"),
        ]

        for pattern, value in patterns:
            if re.search(pattern, text):
                return value

        return None


    def _extract_income_from_text(self, text: str) -> Optional[str]:
        if not text or "年収" not in text:
            return None

        normalized = text.translate(FULL_WIDTH_DIGIT_MAP).replace(",", "")
        match = re.search(r"年収[^0-9]{0,6}([0-9]{1,4})\s*(万|万円)?", normalized)
        if not match:
            return None

        amount = match.group(1)
        unit = match.group(2) or "万"

        if unit.startswith("万"):
            return f"{amount}万円"

        return f"{amount}{unit}" if unit else amount


    def _describe_field(self, field_key: str) -> str:
        return self.required_field_descriptions.get(field_key, field_key)


    def _describe_missing_detail(self, detail_key: str) -> str:
        if detail_key in self.sub_field_descriptions:
            return self.sub_field_descriptions[detail_key]

        if "." in detail_key:
            root, tail = detail_key.split(".", 1)
            root_desc = self._describe_field(root)
            tail_desc = self.sub_field_descriptions.get(detail_key)
            if not tail_desc:
                tail_desc = tail.replace("personality_traits.", "").replace("_", " ")
            return f"{root_desc}（{tail_desc}）"

        return self._describe_field(detail_key)


    def _check_information_progress(self) -> Dict[str, bool]:
        """情報収集の進捗を確認"""
        return build_information_progress(self.user_profile)

    async def _unified_completion_check(self, user_message: str, missing_fields: List[str]) -> Dict[str, Any]:
        """不足項目抽出・完了判定・完了メッセージを1回のLLM呼び出しで実行

        Args:
            user_message: ユーザーの最新メッセージ
            missing_fields: 現時点で不足している必須フィールドのリスト

        Returns:
            Dict containing:
                - missing_info: 抽出された不足項目の辞書
                - is_complete: 情報収集が完了したかどうか
                - completion_message: 完了時の締めのメッセージ（完了時のみ）
        """
        try:
            print("[INFO] unified completion check start")
            print(f"[DEBUG] latest user message: {user_message}")
            print(f"[DEBUG] missing fields (pre-LLM): {missing_fields}")
            print(f"[DEBUG] current profile:\n{await self._format_collected_info()}")

            from google.generativeai import GenerativeModel
            model = GenerativeModel('gemini-2.5-pro')

            required_fields_desc = """
【必須項目】:
- age: ユーザーの年齢（数値）
- gender: 性別（"男性", "女性", "その他"）
- relationship_status: 交際状況（"married", "partnered", "single", "other"）
- location: お住まいの地域（文字列）
- income_range: おおよその年収帯（例: "300万円程度"）
- user_personality_traits: ユーザー自身の性格特性（**必ず辞書形式**）
  {
    "openness": 0.0-1.0,
    "conscientiousness": 0.0-1.0,
    "extraversion": 0.0-1.0,
    "agreeableness": 0.0-1.0,
    "neuroticism": 0.0-1.0
  }
- partner_face_description: パートナーの外見・顔の特徴（画像生成に使用）
- children_info: 子供の希望（**必ず配列形式**）
  [
    {"desired_gender": "男", "name": "たかし"},
    {"desired_gender": "女", "name": "えり"}
  ]
- ideal_partner (独身/その他の場合): 理想のパートナー情報（**必ず辞書形式**）
  {
    "name": "名前",
    "personality_traits": {
      "openness": 0.0-1.0,
      "conscientiousness": 0.0-1.0,
      "extraversion": 0.0-1.0,
      "agreeableness": 0.0-1.0,
      "neuroticism": 0.0-1.0
    },
    "temperament": "性格の総合的な説明",
    "hobbies": ["趣味1", "趣味2"],
    "speaking_style": "話し方の特徴"
  }
- current_partner (既婚/交際中の場合): 現在のパートナー情報（**必ず辞書形式**）
  # 同様の構造
"""

            prompt = f"""
あなたは家族の未来を描くための情報収集アシスタントです。
ユーザーから必要な情報を効率的に収集し、完了判定を行います。

## 現在のユーザープロファイル
{await self._format_collected_info()}

## ユーザーの最新メッセージ
{user_message}

## 必須項目
{required_fields_desc}

## 現時点で不足している項目
{missing_fields}

## あなたのタスク
以下の3つを同時に実行してください：

1. **不足項目の抽出**: ユーザーメッセージから不足している項目を抽出
2. **完了判定**: 全ての必須項目が揃ったか、またはユーザーが完了を示唆しているか判定
3. **完了メッセージ**: 完了の場合のみ、温かく親しみやすい締めのメッセージを生成

## 判定基準
- 必須項目が全て揃っている → 完了
- ユーザーが「これで十分」「もういい」などと言っている → 完了
- それ以外 → 未完了

## 出力形式
以下のJSON形式のみで回答してください。JSON以外のテキストは含めないでください。

```json
{{
  "missing_info": {{
    "field_name": "抽出された値",
    ...
  }},
  "is_complete": true または false,
  "completion_message": "完了時のみ、温かい締めのメッセージ（未完了ならnull）"
}}
```

## 重要なデータ形式ルール
- user_personality_traits: **必ず辞書形式**で、0.0-1.0の数値
- children_info: **必ず配列形式**で、各要素は{{"desired_gender": "男/女", "name": "名前"}}の辞書
- 性格特性の推定:
  - 「明るい」「社交的」→ extraversion: 0.7-0.8
  - 「几帳面」「計画的」→ conscientiousness: 0.7-0.8
  - 「優しい」「思いやり」→ agreeableness: 0.7-0.8
  - 「好奇心旺盛」「創造的」→ openness: 0.7-0.8
  - 「落ち着いている」「楽観的」→ neuroticism: 0.2-0.3
  - 「心配性」「慎重」→ neuroticism: 0.7-0.8
  - キーワードがない場合 → 0.5（中立）

## 例
入力: "ネガティブだが頑張り屋"
出力:
```json
{{
  "missing_info": {{
    "user_personality_traits": {{
      "openness": 0.5,
      "conscientiousness": 0.8,
      "extraversion": 0.3,
      "agreeableness": 0.6,
      "neuroticism": 0.7
    }}
  }},
  "is_complete": false,
  "completion_message": null
}}
```

入力: "男の子「たかし」と女の子「えり」の2人が欲しい"
出力:
```json
{{
  "missing_info": {{
    "children_info": [
      {{"desired_gender": "男", "name": "たかし"}},
      {{"desired_gender": "女", "name": "えり"}}
    ]
  }},
  "is_complete": false,
  "completion_message": null
}}
```

入力: "理想の妻は「あゆみ」で、誠実で天真爛漫な性格"
出力:
```json
{{
  "missing_info": {{
    "ideal_partner": {{
      "name": "あゆみ",
      "personality_traits": {{
        "openness": 0.6,
        "conscientiousness": 0.8,
        "extraversion": 0.7,
        "agreeableness": 0.9,
        "neuroticism": 0.2
      }},
      "temperament": "誠実で天真爛漫",
      "hobbies": [],
      "speaking_style": "温かく親しみやすい"
    }}
  }},
  "is_complete": false,
  "completion_message": null
}}
```
"""

            # リトライ機能付きでLLM呼び出し
            max_retries = 3
            retry_delay = 2  # 秒
            response_text = None

            for attempt in range(max_retries):
                try:
                    response = model.generate_content(prompt)
                    response_text = response.text if hasattr(response, 'text') else str(response)
                    print(f"[DEBUG] unified completion raw response: {response_text[:200]}...")
                    break  # 成功したらループを抜ける
                except Exception as llm_error:
                    if attempt < max_retries - 1:
                        print(f"[WARN] LLM呼び出し失敗（試行{attempt + 1}/{max_retries}）: {llm_error}")
                        print(f"[INFO] {retry_delay}秒後にリトライします...")
                        import asyncio
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # 指数バックオフ
                    else:
                        print(f"[ERROR] LLM呼び出しが{max_retries}回失敗しました: {llm_error}")
                        raise

            if not response_text:
                raise ValueError("LLM応答が取得できませんでした")

            # JSONを抽出
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                print("[WARN] JSON形式が見つかりません")
                return {
                    "missing_info": {},
                    "is_complete": False,
                    "completion_message": None
                }

            result = json.loads(json_match.group(0))

            print("[INFO] unified completion result")
            print(f"  missing_info: {result.get('missing_info', {})}")
            print(f"  is_complete(flag): {result.get('is_complete', False)}")
            if result.get('completion_message'):
                print(f"  completion_message: {result['completion_message'][:80]}...")

            return result

        except Exception as e:
            print(f"[ERROR] unified completion check failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "missing_info": {},
                "is_complete": False,
                "completion_message": None
            }

    def transfer_to_agent(self, agent_name: str) -> Dict[str, Any]:
        """他のエージェントに転送するツール"""
        try:
            print(f"[DEBUG] transfer_to_agent called with: {agent_name}")

            if agent_name == "family_session_agent":
                return {
                    "success": True,
                    "message": "家族会話エージェントに転送します。未来の家族と会話を始めましょう！",
                    "next_agent": "family_session_agent"
                }
            else:
                return {
                    "success": False,
                    "message": f"申し訳ございません。{agent_name}への転送は対応していません。"
                }

        except Exception as e:
            print(f"[ERROR] transfer_to_agent error: {e}")
            return {
                "success": False,
                "message": "申し訳ございません。転送中にエラーが発生しました。"
            }

    async def _check_completion_with_llm(self, user_message: str) -> bool:
        """LLMを使用して情報収集完了を判定

        **非推奨**: _unified_completion_check() を使用してください
        """
        try:
            print("[INFO] LLM完了判定を実行中...")
            print(f"[DEBUG] ユーザーメッセージ: {user_message}")
            print(f"[DEBUG] 現在のプロファイル: {await self._format_collected_info()}")

            # フォールバック: ADKエージェントではなく直接Gemini APIで判定
            from google.generativeai import GenerativeModel
            model = GenerativeModel('gemini-2.5-pro')
            prompt = f"""
以下の情報収集状況を確認してください：

現在のユーザープロファイル：
{await self._format_collected_info()}

ユーザーの最新メッセージ：
{user_message}

必要な情報が十分に収集されたかどうかを判断してください。

【必須項目】（これらが揃えば完了）:
- 年齢（age）
- 交際状況（relationship_status）
- パートナーまたは理想のパートナーの性格特性（personality_traits）
- パートナーの外見・顔の特徴（partner_face_description）
- ユーザー自身の性格特性（user_personality_traits）
- 子供の希望（children_info: 人数と性別）

【推奨項目】（あれば望ましいが、なくても完了可能）:
- 居住地（location）
- 収入範囲（income_range）

【判定基準】:
1. 上記6つの必須項目が全て揃っている → COMPLETED
2. ユーザーが「もう十分」「これで十分」などと言っている → COMPLETED
3. エージェントが「十分な情報が揃いました」と言っている → COMPLETED
4. それ以外 → INCOMPLETE

※推奨項目（location, income_range）は任意のため、なくても完了とする

完了の場合は「COMPLETED」、未完了の場合は「INCOMPLETE」で回答してください。
"""
            response = model.generate_content(prompt)
            response_text = response.text if hasattr(response, 'text') else str(response)
            is_completed = "COMPLETED" in response_text.upper()

            print(f"[DEBUG] LLM判定結果: {response_text}")
            print(f"[INFO] 完了判定: {is_completed}")

            return is_completed

        except Exception as e:
            print(f"[ERROR] LLM完了判定エラー: {e}")
            return False


    async def _format_collected_info(self) -> str:
        """収集済み情報をフォーマット"""
        collected = []
        profile_dict = self.user_profile.dict()
        for key, value in profile_dict.items():
            if value is not None and key != 'created_at':
                collected.append(f"{key}: {value}")
        return "\n".join(collected)

    async def _add_to_history(self, speaker: str, message: str) -> None:
        """会話履歴に追加"""
        self.conversation_history.append({
            "speaker": speaker,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    async def _generate_hera_response_with_extraction(self, user_message: str) -> str:
        """返答生成と情報抽出を統合したメソッド（heraの人格を活かした版）"""
        try:
            # セッションIDの設定とディレクトリ作成
            if not self.current_session:
                self.current_session = await self._get_latest_adk_session_id()

            if self.current_session:
                session_dir = os.path.join(get_sessions_dir(), self.current_session)
                if not os.path.exists(session_dir):
                    print(f"[INFO] 返答生成時にセッションディレクトリ作成: {self.current_session}")
                    await self.start_session(self.current_session)

            from google.generativeai import GenerativeModel
            model = GenerativeModel('gemini-2.5-pro')

            # 現在のプロファイル情報を取得
            formatted_profile = await self._format_collected_info()
            missing_fields = compute_missing_fields(self.user_profile)

            # 不足項目の説明を生成
            missing_fields_text = "\n".join([
                f"- {self._describe_missing_detail(field)} ({field})"
                for field in missing_fields
            ]) if missing_fields else "- （不足はありません）"

            goal_lines: List[str] = []
            if {"age", "gender", "relationship_status"} & set(missing_fields):
                goal_lines.append("- 年齢・性別・交際状況をまとめて確認する")
            if "location" in missing_fields:
                goal_lines.append("- お住まいの地域を丁寧に尋ねる")
            if "income_range" in missing_fields:
                goal_lines.append("- 年収の目安（例: 300万円程度）を尋ねる")
            if "user_personality_traits" in missing_fields:
                goal_lines.append("- あなた自身の性格や強みを掘り下げる（ビッグファイブを意識）")
            if "partner_face_description" in missing_fields:
                goal_lines.append("- パートナーの外見描写を具体的に引き出す")
            if any(field in missing_fields for field in ("ideal_partner", "current_partner")):
                goal_lines.append("- パートナーの性格や外見をまとめて尋ねる")
            if "children_info" in missing_fields:
                goal_lines.append("- 希望するお子さんの人数や性別を尋ねる")
            if not goal_lines:
                goal_lines.append("- 必須項目は揃っているため、感謝を伝えつつ次のステップを案内する")
            goals_text = "\n".join(goal_lines)

            # 会話の流れを考慮したコンテキスト
            recent_history = (
                self.conversation_history[-3:]
                if len(self.conversation_history) > 3
                else self.conversation_history
            )

            prompt = f"""
あなたは{self.persona.name}（{self.persona.role}）です。

基本情報：
- 名前: {self.persona.name}
- 役割: {self.persona.role}
- 領域: {self.persona.domain}
- 象徴: {', '.join(self.persona.symbols)}
- 性格: {self.persona.personality}

現在のユーザープロファイル：
{formatted_profile}

会話履歴：
{recent_history}

ユーザーの最新メッセージ：
{user_message}

不足している必須情報：
{missing_fields_text}

会話の目的：
{goals_text}

あなたの役割：
1. 温かみのある、親しみやすい口調で応答する
2. **3-4ターン以内**で必要最小限の情報を収集する
3. 不足している必須情報を優先的にまとめて尋ねる
4. 愛情深く、家族思いの神として振る舞う

【抽出すべき情報の詳細】

【必須項目】
- age: 年齢（数値）
- gender: 性別（"男性", "女性", "その他"）
- relationship_status: 交際状況（"married", "partnered", "single", "other"）
- location: 居住地（文字列）
- income_range: 年収の目安（例: "300万円", "500〜600万円"）
- partner_face_description: パートナー（または理想のパートナー）の顔・外見的特徴（画像生成に使用）
- user_personality_traits: ユーザー自身の性格特性
  {{
    "openness": 0.0-1.0,
    "conscientiousness": 0.0-1.0,
    "extraversion": 0.0-1.0,
    "agreeableness": 0.0-1.0,
    "neuroticism": 0.0-1.0
  }}

【パートナー関連】
- current_partner: 現在のパートナー情報（既婚/交際中の場合）
  {{
    "name": "名前",
    "age": 年齢,
    "personality_traits": {{
      "openness": 0.0-1.0,        # 好奇心旺盛さ（新しいこと好き）
      "conscientiousness": 0.0-1.0, # 几帳面さ（計画的）
      "extraversion": 0.0-1.0,     # 社交性（明るい・活発）
      "agreeableness": 0.0-1.0,    # 優しさ（思いやり）
      "neuroticism": 0.0-1.0       # 心配性さ（慎重）
    }},
    "temperament": "性格の総合的な説明",
    "hobbies": ["趣味1", "趣味2"],
    "speaking_style": "話し方の特徴"
  }}

- ideal_partner: 理想のパートナー像（独身の場合）
  # 同様の構造

【子供関連】
- children_info: 子供の希望情報（**必ず配列形式**）
  {{
    "desired_gender": "男/女"
  }}

【性格特性の推定ルール】
会話から以下のキーワードで0.0-1.0の値を推定:
- 「明るい」「社交的」「外向的」「活発」 → extraversion: 0.7-0.8
- 「几帳面」「計画的」「責任感」「しっかり」 → conscientiousness: 0.7-0.8
- 「優しい」「思いやり」「協力的」 → agreeableness: 0.7-0.8
- 「好奇心旺盛」「創造的」「新しいこと好き」 → openness: 0.7-0.8
- 「落ち着いている」「楽観的」 → neuroticism: 0.2-0.3
- 「心配性」「慎重」「不安」 → neuroticism: 0.7-0.8
- 「内向的」「静か」 → extraversion: 0.2-0.3
- キーワードがない場合 → 0.5（中立）

【応答の指針】
- 温かみのある、親しみやすい口調で応答する
- 1つの質問で複数項目をまとめて聞く
- パートナーの外見・顔の特徴は必ず聞く（画像生成に使用）
- 子供の名前と性別は必ず聞く
- 不要な情報（趣味、仕事、ライフスタイル詳細など）は基本的に聞かない
- 必要な情報が揃ったら「ありがとうございます。十分な情報が揃いました」と明確に伝える
- 常に愛情深く、家族思いの神として振る舞う

【出力形式】
以下のJSON形式で回答してください：

```json
{{
  "extracted_info": {{
    "field_name": "抽出された値",
    ...
  }},
  "response": "ユーザーへの温かい応答メッセージ（heraの人格を活かした自然な文章）"
}}
```

重要:
- 抽出できた情報のみをJSON形式で返す
- 性格特性は必ず0.0-1.0の数値の辞書形式で推定する
- children_infoは必ず配列（[]）形式で返す
- user_personality_traits は必ず辞書（{{}}）形式で返す
- responseは固定文言ではなく、heraの人格と状況に応じた自然で温かい文章で返す
- ツール呼び出し（check_session_completion）を適切に使用してください
"""

            response = model.generate_content(prompt)
            response_text = response.text if hasattr(response, 'text') else str(response)

            # JSONを抽出
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))

                # 抽出された情報をプロファイルに反映
                extracted_info = result.get("extracted_info", {})
                print(f"[DEBUG] extracted_info from LLM: {extracted_info}")
                if extracted_info:
                    await self._update_user_profile(extracted_info)
                    self.last_extracted_fields = extracted_info
                else:
                    print("[DEBUG] No extracted_info found in LLM response")

                # heraの人格を活かした動的応答を返す
                return result.get("response", "お話を伺いました。続きもぜひ教えてください。")

            # JSON解析に失敗した場合のフォールバック
            return "お話を伺いました。続きもぜひ教えてください。"

        except Exception as e:
            print(f"[ERROR] 統合応答生成エラー: {e}")
            # エラー時も固定文言ではなく、heraらしい応答
            return "申し訳ございません。もう一度お話ししていただけますか？"

    async def _generate_hera_response(self, user_message: str) -> str:
        """ヘーラーエージェントの応答を生成（非推奨：_generate_hera_response_with_extractionを使用）"""
        try:
            from google.generativeai import GenerativeModel
            model = GenerativeModel('gemini-2.5-pro')

            missing_fields = compute_missing_fields(self.user_profile)
            missing_details = collect_missing_field_details(self.user_profile)
            combined_missing = missing_fields + [
                detail for detail in missing_details if detail not in missing_fields
            ]

            if combined_missing:
                missing_fields_text = "\n".join(
                    f"- {self._describe_missing_detail(item)} ({item})"
                    for item in combined_missing
                )
            else:
                missing_fields_text = "- （不足はありません）"

            goal_lines: List[str] = []
            if "age" in missing_fields or "gender" in missing_fields or "relationship_status" in missing_fields:
                goal_lines.append("- 年齢・性別・交際状況をまとめて確認する")
            if "location" in missing_fields:
                goal_lines.append("- お住まいの地域を丁寧に尋ねる")
            if "income_range" in missing_fields:
                goal_lines.append("- 年収の目安（例: 300万円程度）を尋ねる")
            if "user_personality_traits" in missing_fields:
                goal_lines.append("- あなた自身の性格や強みを掘り下げる（ビッグファイブを意識）")
            if "partner_face_description" in missing_fields:
                goal_lines.append("- パートナーの外見描写を具体的に引き出す")
            if any(field in missing_fields for field in ("ideal_partner", "current_partner")):
                goal_lines.append("- パートナーの性格や外見をまとめて尋ねる")
            if "children_info" in missing_fields:
                goal_lines.append("- 希望するお子さんの人数や性別を尋ねる")

            if not goal_lines:
                goal_lines.append("- 必須項目は揃っているため、感謝を伝えつつ次のステップを案内する")

            formatted_profile = await self._format_collected_info()
            recent_history = (
                self.conversation_history[-3:]
                if len(self.conversation_history) > 3
                else self.conversation_history
            )
            goals_text = "\n".join(goal_lines)

            prompt = f"""
あなたは{self.persona.name}（{self.persona.role}）です。

基本情報：
- 名前: {self.persona.name}
- 役割: {self.persona.role}
- 領域: {self.persona.domain}
- 象徴: {', '.join(self.persona.symbols)}
- 性格: {self.persona.personality}

現在のユーザープロファイル：
{formatted_profile}

会話履歴：
{recent_history}

ユーザーの最新メッセージ：
{user_message}

不足している必須情報：
{missing_fields_text}

会話の目的：
{goals_text}

あなたの役割：
1. 温かみのある、親しみやすい口調で応答する
2. **3-4ターン以内**で必要最小限の情報（年齢・性別・交際状況・居住地・年収帯・パートナー情報・ユーザー自身の性格・子ども希望）を収集する
3. 不足している必須情報を優先的にまとめて尋ねる

重要な指示：
- **1つの質問で複数項目をまとめて聞く**こと（例: 「パートナーの性格と外見の特徴を教えてください」）
- パートナーの外見・顔の特徴は必ず聞く（画像生成に使用）
- 性別や年収などセンシティブな情報は丁寧な言い回しで確認する
- 不要な情報（趣味、仕事、ライフスタイル詳細）は基本的に聞かない
- ユーザーが自発的に話した情報は受け入れるが、こちらから細かく聞き出さない
- 必要な情報が揃ったら「ありがとうございます。十分な情報が揃いました」と明確に伝える
- 常に愛情深く、家族思いの神として振る舞う

ユーザーのメッセージに対して、{self.persona.name}として自然で温かく、かつ**効率的な**応答をしてください。
"""

            response = model.generate_content(prompt)
            return response.text if hasattr(response, 'text') else str(response)

        except Exception as e:
            print(f"[ERROR] ヘーラー応答生成エラー: {e}")
            return "お話を伺いました。続きもぜひ教えてください。"

    async def _generate_completion_message(self) -> str:
        """情報収集完了時のメッセージを生成

        **非推奨**: _unified_completion_check() で完了メッセージも生成されます
        """
        return (
            "素晴らしいです！必要な情報が揃いました。\n"
            "それでは、あなたの未来の家族と会話を始めましょう。\n"
            "家族との会話を始めるには、family_session_agentに転送します。"
        )


    async def _get_latest_adk_session_id(self, retries: int = 3, timeout_sec: float = 10.0) -> Optional[str]:
        """ADKの最新セッションIDを取得（リトライ付）"""
        try:
            import httpx
            last_err = None
            for attempt in range(1, retries + 1):
                try:
                    async with httpx.AsyncClient(timeout=timeout_sec) as client:
                        r = await client.get(f"{self.adk_base_url}/apps/hera/users/user/sessions")
                        if r.status_code == 200:
                            data = r.json()
                            print(f"[DEBUG] ADKセッション一覧(try {attempt}/{retries}): {data}")
                            if isinstance(data, list) and data:
                                # lastUpdateTimeがあれば最新順に
                                try:
                                    data_sorted = sorted(
                                        data,
                                        key=lambda x: x.get("lastUpdateTime", 0),
                                        reverse=True
                                    )
                                except Exception:
                                    data_sorted = data
                                first = data_sorted[0]
                                if isinstance(first, dict):
                                    sid = first.get("session_id") or first.get("id")
                                    if sid:
                                        return sid
                except Exception as e:
                    last_err = e
                    print(f"[WARN] ADKセッションID取得エラー(try {attempt}/{retries}): {e}")
                    # 簡易バックオフ
                    import asyncio as _asyncio
                    await _asyncio.sleep(min(1.5 * attempt, 5))

            print(f"[ERROR] ADKセッションIDの取得に失敗: {last_err}")
            return None
        except Exception as e:
            print(f"[ERROR] ADKセッションID取得処理エラー: {e}")
            return None


    async def _save_session_data(self) -> None:
        """セッションデータを保存"""
        if not self.current_session:
            print(f"[WARN] セッションIDが設定されていません: {self.current_session}")
            return

        print(f"[INFO] saving session data (session_id={self.current_session})")

        # セッションディレクトリを取得（事前に作成済みを想定）
        session_dir = os.path.join(get_sessions_dir(), self.current_session)

        # ディレクトリの存在確認のみ（start_sessionで作成済み）
        if not os.path.exists(session_dir):
            print(f"[WARN] セッションディレクトリが存在しません: {session_dir}")
            return

        # ユーザープロファイルを保存
        profile_data = prune_empty_fields(self.user_profile.dict())
        print(f"[DEBUG] user profile persisted: {profile_data}")

        with open(os.path.join(session_dir, "user_profile.json"), "w", encoding="utf-8") as f:
            json.dump(profile_data, f, ensure_ascii=False, indent=2)

        # 会話履歴を保存
        print(f"[DEBUG] conversation entries: {len(self.conversation_history)}")
        with open(os.path.join(session_dir, "conversation_history.json"), "w", encoding="utf-8") as f:
            json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)

        print(f"[INFO] session data saved: {session_dir}")


    async def _save_conversation_history(self) -> None:
        """会話履歴のみを保存（毎ターン呼び出し）"""
        if not self.current_session:
            print("[WARN] セッションID未設定のため履歴保存をスキップ")
            return

        session_dir = os.path.join(get_sessions_dir(), self.current_session)
        if not os.path.exists(session_dir):
            print(f"[WARN] セッションディレクトリが存在しません: {session_dir}")
            return

        try:
            with open(f"{session_dir}/conversation_history.json", "w", encoding="utf-8") as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
            print(f"[DEBUG] 会話履歴を保存しました: {len(self.conversation_history)}件")
        except Exception as e:
            print(f"[ERROR] 会話履歴保存エラー: {e}")


    def get_user_profile(self) -> UserProfile:
        """ユーザープロファイルを取得"""
        return self.user_profile

    def is_information_complete(self) -> bool:
        """情報収集が完了しているかチェック"""
        progress = self._check_information_progress()
        return all(progress.values())

    async def end_session(self) -> Dict[str, Any]:
        """セッション終了"""
        if not self.current_session:
            return {}

        # 最終データを保存
        await self._save_session_data()

        # セッション情報を返す
        session_dir = os.path.join(get_sessions_dir(), self.current_session)
        session_info = {
            "session_id": self.current_session,
            "user_profile": self.user_profile.dict(),
            "conversation_count": len(self.conversation_history),
            "information_complete": self.is_information_complete(),
            "session_dir": session_dir
        }

        return session_info

    # ADKの標準フローに対応するメソッドを追加
    async def run(self, message: str, session_id: str = None, **kwargs) -> str:
        """ADKの標準runメソッド"""
        print("[INFO] ADK runメソッドが呼び出されました")
        print(f"[DEBUG] メッセージ: {message}")
        print(f"[DEBUG] セッションID: {session_id}")

        try:
            # セッションIDの設定
            if session_id:
                self.current_session = session_id
            elif not self.current_session:
                self.current_session = await self._get_latest_adk_session_id()
                if not self.current_session:
                    return json.dumps(self._wrap_response("セッションを開始できませんでした。"), ensure_ascii=False)

            # 会話履歴にユーザーメッセージを追加
            await self._add_to_history("user", message)
            await self._save_conversation_history()

            # 統合処理（情報抽出 + 返答生成）
            print(f"[DEBUG] Calling _generate_hera_response_with_extraction for message: {message}")
            response_text = await self._generate_hera_response_with_extraction(message)
            print(f"[DEBUG] Response from _generate_hera_response_with_extraction: {response_text}")

            # エージェントの応答を履歴に追加
            await self._add_to_history("hera", response_text)
            await self._save_conversation_history()

            # メッセージは既に履歴へ登録済みなので、完了判定の評価のみ実行
            completion_result = await self._evaluate_session_completion(
                message,
                user_message_already_logged=True,
            )

            # セッションデータを保存（プロファイル情報を含む）
            await self._save_session_data()

            # レスポンスを返す
            payload = self._wrap_response(response_text)
            profile_snapshot = prune_empty_fields(self.user_profile.dict())
            payload.update({
                "session_status": completion_result.get("status", "INCOMPLETE"),
                "completion_message": completion_result.get("completion_message"),
                "missing_fields": completion_result.get("remaining_missing", []),
                "user_profile": profile_snapshot,
                "information_progress": build_information_progress(profile_snapshot),
                "last_extracted_fields": self.last_extracted_fields,
            })
            payload_json = json.dumps(payload, ensure_ascii=False)

            print(f"📤 レスポンス: {payload}")

            return payload_json

        except Exception as e:
            print(f"[ERROR] runメソッドエラー: {e}")
            # エラー時もheraらしい応答
            error_response = "申し訳ございません。少し時間をいただけますか？"
            return json.dumps(self._wrap_response(error_response), ensure_ascii=False)


    async def _evaluate_session_completion(
        self,
        user_message: Optional[str],
        *,
        user_message_already_logged: bool,
    ) -> Dict[str, Any]:
        """最新メッセージをもとに完了判定を行い、結果を辞書で返す"""
        sanitized_message = user_message or ""
        print(f"[INFO] セッション完了評価を実行: {sanitized_message}")

        result: Dict[str, Any] = {
            "status": "INCOMPLETE",
            "completion_message": None,
            "remaining_missing": [],
        }

        try:
            # 会話履歴が未記録の場合のみ追加
            if not user_message_already_logged and sanitized_message:
                await self._add_to_history("user", sanitized_message)
                await self._save_conversation_history()

            # セッションIDのフォールバック（runを経由しない呼出し対策）
            if not self.current_session:
                latest_sid = await self._get_latest_adk_session_id(retries=3, timeout_sec=10.0)
                if not latest_sid:
                    print("[ERROR] ADKセッションIDが取得できません（完了評価フォールバック）")
                    result["status"] = "ERROR"
                    result["error"] = "セッションIDを取得できませんでした"
                    self._last_completion_result = dict(result)
                    return result
                self.current_session = latest_sid
                print(f"[INFO] 完了評価側でセッションID設定: {self.current_session}")
                session_dir = os.path.join(get_sessions_dir(), self.current_session)
                if not os.path.exists(session_dir):
                    await self.start_session(self.current_session)

            # 不足フィールドを特定
            missing_fields = compute_missing_fields(self.user_profile)

            # 統合完了チェック（1回のLLM呼び出しで抽出・判定・メッセージ生成）
            unified_result = await self._unified_completion_check(sanitized_message, missing_fields)

            # 抽出された情報をプロファイルに反映
            if unified_result.get("missing_info"):
                await self._update_user_profile(unified_result["missing_info"])
                self.last_extracted_fields = unified_result["missing_info"]

            # 更新後の不足フィールドを再チェック
            remaining_missing = compute_missing_fields(self.user_profile)
            result["remaining_missing"] = remaining_missing

            # LLMの判定と実際の不足フィールドの整合性を取る
            llm_complete = unified_result.get("is_complete", False)
            actually_complete = not remaining_missing
            is_complete = llm_complete or actually_complete
            completion_message = unified_result.get("completion_message")
            result["completion_message"] = completion_message

            print("[DEBUG] 完了判定詳細:")
            print(f"  LLM判定: {llm_complete}")
            print(f"  実際の不足: {remaining_missing}")
            print(f"  最終判定: {is_complete}")

            if is_complete:
                print("[INFO] session completion confirmed")
                result["status"] = "COMPLETED"
                if self._session_state != self.SessionState.COMPLETED:
                    await self._generate_family_images()
                    if completion_message:
                        await self._add_to_history("hera", completion_message)
                        await self._save_conversation_history()
                    await self._save_session_data()
                    self._session_state = self.SessionState.COMPLETED
            else:
                print("[INFO] session continues; missing fields remain")
                if remaining_missing:
                    print(f"[DEBUG] remaining missing fields: {remaining_missing}")

            self._last_completion_result = dict(result)
            return result

        except Exception as e:
            print(f"[ERROR] completion evaluation failed: {e}")
            import traceback
            traceback.print_exc()
            result["status"] = "ERROR"
            result["error"] = str(e)
            self._last_completion_result = dict(result)
            return result

    async def check_session_completion(self, user_message: str) -> str:
        """セッション完了判定ツール（ADK FunctionTool互換）

        Returns:
            str: 完了状況のメッセージ
        """
        evaluation = await self._evaluate_session_completion(
            user_message,
            user_message_already_logged=False,
        )
        status = evaluation.get("status", "INCOMPLETE")

        if status == "COMPLETED":
            completion_message = evaluation.get("completion_message")
            return f"COMPLETED: {completion_message}" if completion_message else "COMPLETED"
        if status == "ERROR":
            error_message = evaluation.get("error") or "不明なエラーが発生しました"
            return f"完了判定中にエラーが発生しました: {error_message}"
        return "INCOMPLETE"

    async def _generate_family_images(self):
        """家族の画像を生成（修正版）"""
        try:
            from .image_generator import FamilyImageGenerator

            image_generator = FamilyImageGenerator()
            image_generator.current_session = self.current_session

            print("[INFO] 家族画像生成開始")

            # 1. 奥さんの画像生成
            partner_image_path = None
            if self.user_profile.ideal_partner:
                print("[INFO] パートナー画像生成中...")
                partner_image_path = await image_generator.generate_partner_image(
                    self.user_profile.ideal_partner
                )
                self.user_profile.partner_image_path = partner_image_path
                print(f"[INFO] パートナー画像生成完了: {partner_image_path}")

            # 2. ユーザー画像は既存のものを取得
            user_image_path = await image_generator.get_user_image_path(self.current_session)
            if user_image_path:
                self.user_profile.user_image_path = user_image_path
                print(f"[INFO] ユーザー画像取得完了: {user_image_path}")
            else:
                print("[WARN] ユーザー画像が見つかりません")
                return

            # 3. 子供の画像生成（両親の画像をインプットに使用）
            if self.user_profile.children_info and partner_image_path and user_image_path:
                print("[INFO] 子供画像生成中...")
                children_images = await image_generator.generate_children_images(
                    self.user_profile.children_info,
                    partner_image_path,
                    user_image_path
                )
                self.user_profile.children_images = children_images
                print(f"[INFO] 子供画像生成完了: {len(children_images)}名")

            print("[INFO] 家族画像生成完了")

        except Exception as e:
            print(f"[ERROR] 画像生成エラー: {e}")
            import traceback
            traceback.print_exc()
            # エラーでもセッションは完了として扱う


# ADK用のエクスポート関数
def hera_session_agent(api_key: str | None = None):
    """Heraセッションエージェントのファクトリ関数

    ADK Web UIから呼び出される関数
    """
    return ADKHeraAgent()
