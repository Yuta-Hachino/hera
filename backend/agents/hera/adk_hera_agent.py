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

        # 情報収集の進捗管理（必須項目定義）
        # ペルソナ生成と画像生成に必要な最小限の項目のみ
        self.base_required_info = [
            "age",
            "relationship_status",
            "user_personality_traits",
            "partner_face_description",
            "children_info"
        ]

        # 推奨項目（なくても完了可能だが、あると体験の質が向上）
        self.recommended_info = [
            "location",
            "income_range"
        ]

        self.relationship_required_info = {
            "married": ["current_partner", "partner_info"],
            "partnered": ["current_partner", "partner_info"],
            "single": ["ideal_partner"],
            "other": ["ideal_partner"]
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

        # サブエージェントとしてfamily_agentを追加（遅延インポート対応）
        try:
            # agents.familyパッケージから直接インポート
            import sys
            agents_dir = os.path.dirname(os.path.dirname(__file__))
            if agents_dir not in sys.path:
                sys.path.insert(0, agents_dir)

            from family.entrypoints import create_family_session
            family_agent = create_family_session()
            self.agent.sub_agents = [family_agent]
            print("[SUCCESS] Familyエージェントをサブエージェントとして追加しました")

            # デバッグ：サブエージェント追加後もツールが残っているか確認
            print(f"[DEBUG] サブエージェント追加後のHeraツール数: {len(self.agent.tools) if self.agent.tools else 0}")
        except Exception as e:
            print(f"[WARNING] Familyエージェントのインポートに失敗しました: {e}")
            import traceback
            traceback.print_exc()
            # サブエージェントなしで続行
            self.agent.sub_agents = []

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
1. 年齢と交際状況
2. パートナーの性格（既婚/交際中なら実際、独身なら理想）
3. パートナーの外見・顔の特徴（画像生成に使用）
4. ユーザー自身の性格
5. 子供の希望（人数・性別）

⭐⭐ 推奨項目（できれば聞く）:
6. 居住地
7. 収入範囲

⭐ オプション（ユーザーが自発的に話した場合のみ記録）:
- 趣味・興味
- 仕事関連

【質問の仕方（重要）】
❌ ダメな例: 1つずつ順番に聞く
  「年齢を教えてください」→「次に性別を...」→「収入は...」

✅ 良い例: 関連する情報をまとめて聞く
  「まず、年齢と現在パートナーがいらっしゃるか、お住まいの地域を教えていただけますか？」

【効率的な質問フロー例】

ターン1（基本情報まとめて）:
「まず、あなたのことを教えてください。年齢と、現在のパートナーの有無（既婚/交際中/独身）を教えていただけますか？」

ターン2（パートナー情報まとめて）:
【既婚/交際中】
「パートナーの方について教えてください。性格（明るい、優しい、几帳面など）と、外見の特徴（顔立ち、髪型、雰囲気など）を教えていただけますか？」

【独身】
「理想のパートナーについて教えてください。どんな性格で、どんな外見の方が理想ですか？」

ターン3（ユーザー自身と子供まとめて）:
「あなた自身の性格と、お子さんの希望（人数や性別）を教えてください」

ターン4（推奨項目・任意）:
「よろしければ、お住まいの地域も教えていただけますか？」

→ これで完了！

【厳守事項】
- 1つの質問で複数項目をまとめて聞くこと
- パートナーの外見・顔の特徴は必ず聞く（画像生成に使用）
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
- 必ず最初にextract_user_infoを呼び出すこと
- ツール実行前に通常のテキスト応答を出力してはならない
- extract_user_infoのfunction_callを出力した場合は、その直後に必ず最終テキストメッセージを返し、ツールから受け取った文字列をそのまま提示すること
- check_session_completionは情報が揃ったタイミングで必ず呼び出す
- 完了後は必ずtransfer_to_agentでfamily_session_agentに転送する

利用可能なツール：
- extract_user_info: ユーザー情報を抽出・保存（最初に必ず呼ぶ／戻り値=最終応答）
- check_session_completion: 情報収集完了を判定
- transfer_to_agent: 他のエージェントに転送（完了後にfamily_session_agentへ）

これらのツールを適切に使用して、ユーザー情報の収集と管理を行ってください。
"""

    def _get_agent_tools(self) -> List[Any]:
        """エージェントのツールを取得"""
        from google.adk.tools import FunctionTool

        # カスタムツールを定義
        tools = []

        # 情報抽出ツール（関数名がツール名になる）
        extract_info_tool = FunctionTool(
            func=self.extract_user_info
        )
        tools.append(extract_info_tool)

        # セッション完了判定ツール（関数名がツール名になる）
        completion_tool = FunctionTool(
            func=self.check_session_completion
        )
        tools.append(completion_tool)

        # セッションデータ保存ツールは削除（_extract_user_info_toolで既に保存済み）

        return tools

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
        """セッション開始"""
        self.current_session = session_id
        self.user_profile = UserProfile()
        self.conversation_history = []
        self._session_state = self.SessionState.COLLECTING

        # セッション用ディレクトリを事前に作成
        session_dir = os.path.join(get_sessions_dir(), session_id)
        photos_dir = os.path.join(session_dir, "photos")

        # ディレクトリが存在しない場合のみ作成
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)
            os.makedirs(photos_dir)
            print(f"📁 セッションディレクトリを作成しました: {session_dir}")

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
            return self._wrap_response("もう少し詳しく教えていただけますか？")


    async def _extract_information(self, user_message: str) -> Dict[str, Any]:
        """ユーザーメッセージから情報を抽出"""
        print(f"🔍 情報抽出開始: {user_message}")

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
- location: 居住地（文字列）※できれば

【パートナー関連】
- relationship_status: 交際状況（"married", "partnered", "single", "other"）

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

- user_personality_traits: ユーザー自身の性格特性
  {{
    "openness": 0.0-1.0,
    "conscientiousness": 0.0-1.0,
    "extraversion": 0.0-1.0,
    "agreeableness": 0.0-1.0,
    "neuroticism": 0.0-1.0
  }}

【子供関連】
- children_info: 子供の希望情報（**必ず配列形式**）
  [{{
    "desired_gender": "男/女"
  }}]

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

            print(f"🤖 抽出レスポンス: {response_text}")

            # JSON形式で抽出された情報をパース
            extracted_info: Dict[str, Any] = {}
            try:
                # JSON部分を抽出
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    extracted_info = json.loads(json_str)
                    print(f"📝 抽出された情報: {extracted_info}")
                    await self._update_user_profile(extracted_info)
                else:
                    print("⚠️ JSON形式が見つかりません")
            except json.JSONDecodeError as e:
                # 手動抽出は行わず、次発話でのLLM抽出に委ねる
                print(f"⚠️ JSON解析エラー（手動抽出はスキップ）: {e}")

            self.last_extracted_fields = extracted_info
            return extracted_info

        except Exception as e:
            print(f"❌ 情報抽出エラー（手動抽出はスキップ）: {e}")
            return {}

    async def _update_user_profile(self, extracted_info: Dict[str, Any]) -> None:
        """ユーザープロファイルを更新"""
        for key, value in extracted_info.items():
            if hasattr(self.user_profile, key) and value is not None:
                setattr(self.user_profile, key, value)

        # 作成日時を設定
        if self.user_profile.created_at is None:
            self.user_profile.created_at = datetime.now().isoformat()


    def _check_information_progress(self) -> Dict[str, bool]:
        """情報収集の進捗を確認"""
        progress = {}
        for info_key in self.required_info:
            value = getattr(self.user_profile, info_key, None)
            progress[info_key] = not self._is_value_missing(value)
        return progress

    def _is_value_missing(self, value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str) and not value.strip():
            return True
        if isinstance(value, (list, dict)) and len(value) == 0:
            return True
        return False

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
            print(f"🚀 統合完了チェックを実行中...")
            print(f"📝 ユーザーメッセージ: {user_message}")
            print(f"📋 不足フィールド: {missing_fields}")
            print(f"👤 現在のプロファイル:\n{await self._format_collected_info()}")

            from google.generativeai import GenerativeModel
            model = GenerativeModel('gemini-2.5-pro')

            # 必須項目の説明を生成
            required_fields_desc = """
【必須項目】:
- age: ユーザーの年齢
- relationship_status: 交際状況（married/partnered/single/other）
- user_personality_traits: ユーザー自身の性格特性（ビッグファイブ: openness, conscientiousness, extraversion, agreeableness, neuroticism）
- partner_face_description: パートナーの外見・顔の特徴（画像生成に使用）
- children_info: 子供の希望（人数・性別）
- ideal_partner (独身の場合): 理想のパートナー情報
- current_partner (既婚/交際中の場合): 現在のパートナー情報
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

## 例
入力: "優しい性格で、丸顔の人がいいです"
出力:
```json
{{
  "missing_info": {{
    "ideal_partner": {{
      "temperament": "優しい"
    }},
    "partner_face_description": "丸顔"
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
                    print(f"🤖 統合チェック応答: {response_text[:200]}...")
                    break  # 成功したらループを抜ける
                except Exception as llm_error:
                    if attempt < max_retries - 1:
                        print(f"⚠️ LLM呼び出し失敗（試行{attempt + 1}/{max_retries}）: {llm_error}")
                        print(f"⏳ {retry_delay}秒後にリトライします...")
                        import asyncio
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # 指数バックオフ
                    else:
                        print(f"❌ LLM呼び出しが{max_retries}回失敗しました: {llm_error}")
                        raise

            if not response_text:
                raise ValueError("LLM応答が取得できませんでした")

            # JSONを抽出
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                print("⚠️ JSON形式が見つかりません")
                return {
                    "missing_info": {},
                    "is_complete": False,
                    "completion_message": None
                }

            result = json.loads(json_match.group(0))

            print(f"✅ 統合チェック結果:")
            print(f"  - 抽出情報: {result.get('missing_info', {})}")
            print(f"  - 完了判定: {result.get('is_complete', False)}")
            if result.get('completion_message'):
                print(f"  - 完了メッセージ: {result['completion_message'][:50]}...")

            return result

        except Exception as e:
            print(f"❌ 統合完了チェックエラー: {e}")
            import traceback
            traceback.print_exc()
            return {
                "missing_info": {},
                "is_complete": False,
                "completion_message": None
            }

    async def _check_completion_with_llm(self, user_message: str) -> bool:
        """LLMを使用して情報収集完了を判定

        **非推奨**: _unified_completion_check() を使用してください
        """
        try:
            print(f"🔍 LLM完了判定を実行中...")
            print(f"📝 ユーザーメッセージ: {user_message}")
            print(f"👤 現在のプロファイル: {await self._format_collected_info()}")

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

            print(f"🤖 LLM判定結果: {response_text}")
            print(f"✅ 完了判定: {is_completed}")

            return is_completed

        except Exception as e:
            print(f"❌ LLM完了判定エラー: {e}")
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

    async def _generate_hera_response(self, user_message: str) -> str:
        """ヘーラーエージェントの応答を生成"""
        try:
            from google.generativeai import GenerativeModel
            model = GenerativeModel('gemini-2.5-pro')

            prompt = f"""
あなたは{self.persona.name}（{self.persona.role}）です。

基本情報：
- 名前: {self.persona.name}
- 役割: {self.persona.role}
- 領域: {self.persona.domain}
- 象徴: {', '.join(self.persona.symbols)}
- 性格: {self.persona.personality}

現在のユーザープロファイル：
{await self._format_collected_info()}

会話履歴：
{self.conversation_history[-3:] if len(self.conversation_history) > 3 else self.conversation_history}

ユーザーの最新メッセージ：
{user_message}

あなたの役割：
1. 温かみのある、親しみやすい口調で応答する
2. **3-4ターン以内**で必要最小限の情報を効率的に収集する
3. 必須情報のみ収集する：
   - 年齢と交際状況
   - パートナーの性格と外見・顔の特徴
   - ユーザー自身の性格
   - 子供の希望（人数・性別）
   - （できれば）居住地

重要な指示：
- **1つの質問で複数項目をまとめて聞く**こと（例: 「パートナーの性格と外見の特徴を教えてください」）
- パートナーの外見・顔の特徴は必ず聞く（画像生成に使用）
- 不要な情報（趣味、仕事、ライフスタイル詳細）は基本的に聞かない
- ユーザーが自発的に話した情報は受け入れるが、こちらから細かく聞き出さない
- 必要な情報が揃ったら「ありがとうございます。十分な情報が揃いました」と明確に伝える
- 常に愛情深く、家族思いの神として振る舞う

ユーザーのメッセージに対して、{self.persona.name}として自然で温かく、かつ**効率的な**応答をしてください。
"""

            response = model.generate_content(prompt)
            return response.text if hasattr(response, 'text') else str(response)

        except Exception as e:
            print(f"❌ ヘーラー応答生成エラー: {e}")
            return "もう少し詳しく教えていただけますか？"

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
                            print(f"🔍 ADKセッション一覧(try {attempt}/{retries}): {data}")
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
                    print(f"⚠️ ADKセッションID取得エラー(try {attempt}/{retries}): {e}")
                    # 簡易バックオフ
                    import asyncio as _asyncio
                    await _asyncio.sleep(min(1.5 * attempt, 5))

            print(f"❌ ADKセッションIDの取得に失敗: {last_err}")
            return None
        except Exception as e:
            print(f"❌ ADKセッションID取得処理エラー: {e}")
            return None


    async def _save_session_data(self) -> None:
        """セッションデータを保存"""
        if not self.current_session:
            print(f"⚠️ セッションIDが設定されていません: {self.current_session}")
            return

        print(f"💾 セッションデータを保存中... セッションID: {self.current_session}")

        # セッションディレクトリを取得（事前に作成済みを想定）
        session_dir = os.path.join(get_sessions_dir(), self.current_session)

        # ディレクトリの存在確認のみ（start_sessionで作成済み）
        if not os.path.exists(session_dir):
            print(f"⚠️ セッションディレクトリが存在しません: {session_dir}")
            return

        print(f"📁 セッションディレクトリ: {session_dir}")

        # ユーザープロファイルを保存
        profile_data = self.user_profile.dict()
        print(f"👤 ユーザープロファイル: {profile_data}")

        with open(f"{session_dir}/user_profile.json", "w", encoding="utf-8") as f:
            json.dump(profile_data, f, ensure_ascii=False, indent=2)

        # 会話履歴を保存
        print(f"💬 会話履歴数: {len(self.conversation_history)}")
        with open(f"{session_dir}/conversation_history.json", "w", encoding="utf-8") as f:
            json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)

        print(f"✅ セッションデータ保存完了: {session_dir}")


    async def _save_conversation_history(self) -> None:
        """会話履歴のみを保存（毎ターン呼び出し）"""
        if not self.current_session:
            print("⚠️ セッションID未設定のため履歴保存をスキップ")
            return

        session_dir = os.path.join(get_sessions_dir(), self.current_session)
        if not os.path.exists(session_dir):
            print(f"⚠️ セッションディレクトリが存在しません: {session_dir}")
            return

        with open(f"{session_dir}/conversation_history.json", "w", encoding="utf-8") as f:
            json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)


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
        print(f"🚀 ADK runメソッドが呼び出されました")
        print(f"📝 メッセージ: {message}")
        print(f"🆔 セッションID: {session_id}")

        # ADK既存セッションIDのみを使用
        resolved_session_id = None
        if session_id and session_id.strip():
            resolved_session_id = session_id.strip()
        else:
            try:
                import httpx
                with httpx.Client(timeout=5) as client:
                    r = client.get(f"{self.adk_base_url}/apps/agents/users/user/sessions")
                    if r.status_code == 200 and isinstance(r.json(), list) and r.json():
                        data = r.json()
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
                            resolved_session_id = first.get("session_id") or first.get("id")
            except Exception as e:
                print(f"⚠️ ADKセッションID取得エラー(run): {e}")

        if not resolved_session_id:
            print("❌ ADKセッションIDが取得できません")
            return "セッションIDが取得できませんでした"

        # UIのセッションIDに常時同期（異なる場合は更新）
        if self.current_session != resolved_session_id:
            self.current_session = resolved_session_id
            # ディレクトリ未作成時のみ開始処理
            session_dir = os.path.join(get_sessions_dir(), self.current_session)
            if not os.path.exists(session_dir):
                await self.start_session(self.current_session)

        # ツールを直接呼び出して応答を生成（標準フロー無効化のため）
        payload_raw = await self._extract_user_info_tool(message)

        if isinstance(payload_raw, dict):
            payload = payload_raw
            payload_json = json.dumps(payload, ensure_ascii=False)
        else:
            try:
                payload = json.loads(payload_raw)
                payload_json = payload_raw
            except Exception:
                payload = self._wrap_response(None)
                payload_json = json.dumps(payload, ensure_ascii=False)

        print(f"📤 レスポンス: {payload}")

        return payload_json

    # ADKツール用のメソッド
    async def extract_user_info(self, user_message: str) -> str:
        """ユーザー情報抽出ツール"""
        print(f"🔍 情報抽出ツールが呼び出されました: {user_message}")

        try:
            # runで設定されていない場合はフォールバックで最新セッションIDを取得
            if not self.current_session:
                latest_sid = await self._get_latest_adk_session_id(retries=3, timeout_sec=10.0)
                if not latest_sid:
                    print("❌ ADKセッションIDが取得できません（ツール側フォールバック）")
                    return "セッションIDが取得できませんでした"
                self.current_session = latest_sid
                print(f"🆔 Heraエージェントのセッション ID: {self.current_session}")

            # セッション開始（ディレクトリ未作成時）
            session_dir = os.path.join(get_sessions_dir(), self.current_session)
            if not os.path.exists(session_dir):
                await self.start_session(self.current_session)

            # 会話履歴にユーザーメッセージを追加
            await self._add_to_history("user", user_message)
            # 会話履歴のみ即時保存
            await self._save_conversation_history()

            # ユーザー情報を抽出
            await self._extract_information(user_message)

            # エージェントの応答を生成
            if self._session_state == self.SessionState.COMPLETED:
                payload = self._wrap_response("")
            else:
                response_text = await self._generate_hera_response(user_message)
                payload = self._wrap_response(response_text)

            # エージェントの応答を履歴に追加
            await self._add_to_history("hera", payload["message"])
            # 会話履歴のみ即時保存
            await self._save_conversation_history()

            # 毎ターンの保存は行わず、メモリにのみ保持
            return json.dumps(payload, ensure_ascii=False)
        except Exception as e:
            print(f"❌ 情報抽出エラー: {e}")
            return json.dumps(
                self._wrap_response(f"申し訳ございません。エラーが発生しました: {str(e)}"),
                ensure_ascii=False,
            )

    async def _extract_missing_information(self, user_message: str, missing_fields: List[str]) -> Dict[str, Any]:
        """不足しているフィールドのみ抽出

        **非推奨**: _unified_completion_check() を使用してください
        """
        if not missing_fields:
            return {}

        print(f"🔍 不足項目の抽出を実行: {missing_fields}")

        try:
            from google.generativeai import GenerativeModel
            model = GenerativeModel('gemini-2.5-pro')

            prompt = f"""
以下の不足しているフィールドのみをJSON形式で抽出してください。存在しない場合はフィールドを含めないでください。

不足フィールド: {missing_fields}
ユーザーメッセージ: {user_message}
現在のプロファイル: {self.user_profile.dict()}
"""

            response = model.generate_content(prompt)
            response_text = response.text if hasattr(response, 'text') else str(response)
            print(f"🤖 不足フィールド抽出レスポンス: {response_text}")

            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                print("⚠️ 不足項目抽出: JSON形式が見つかりません")
                return {}

            info = json.loads(json_match.group(0))
            if info:
                await self._update_user_profile(info)
                self.last_extracted_fields = info
            return info

        except Exception as e:
            print(f"❌ 不足項目抽出エラー: {e}")
            return {}

    async def check_session_completion(self, user_message: str) -> str:
        """セッション完了判定ツール（統合版）

        1回のLLM呼び出しで以下を実行:
        - 不足項目の抽出
        - 完了判定
        - 完了メッセージの生成
        """
        print(f"🔍 完了判定ツールが呼び出されました: {user_message}")

        try:
            # 会話履歴にユーザーメッセージを追加（完了判定経路でも欠落させない）
            await self._add_to_history("user", user_message)
            # 履歴のみ即時保存
            await self._save_conversation_history()

            # セッションIDのフォールバック（runを経由しない呼出し対策）
            if not self.current_session:
                latest_sid = await self._get_latest_adk_session_id(retries=3, timeout_sec=10.0)
                if not latest_sid:
                    print("❌ ADKセッションIDが取得できません（完了判定フォールバック）")
                    return "INCOMPLETE"
                self.current_session = latest_sid
                print(f"🆔 完了判定側でセッションID設定: {self.current_session}")
                # ディレクトリ未作成時のみ開始
                session_dir = os.path.join(get_sessions_dir(), self.current_session)
                if not os.path.exists(session_dir):
                    await self.start_session(self.current_session)

            # 不足フィールドを特定
            missing_fields = [
                key for key in self.required_info
                if self._is_value_missing(getattr(self.user_profile, key, None))
            ]

            # 統合完了チェック（1回のLLM呼び出しで抽出・判定・メッセージ生成）
            result = await self._unified_completion_check(user_message, missing_fields)

            # 抽出された情報をプロファイルに反映
            if result.get("missing_info"):
                await self._update_user_profile(result["missing_info"])
                self.last_extracted_fields = result["missing_info"]

            is_complete = result.get("is_complete", False)
            completion_message = result.get("completion_message")

            if is_complete:
                print("✅ セッション完了と判定されました")
                if self._session_state != self.SessionState.COMPLETED:
                    # 完了メッセージを履歴に記録
                    if completion_message:
                        await self._add_to_history("hera", completion_message)
                        await self._save_conversation_history()

                    # 完了時のみディスク保存（プロフィール・履歴）
                    await self._save_session_data()
                    self._session_state = self.SessionState.COMPLETED

                    # 完了メッセージを返して、Familyエージェントへの遷移を促す
                    return f"COMPLETED: {completion_message}"
                else:
                    # 既に完了済みの場合は簡潔なメッセージ
                    return "COMPLETED"
            else:
                print("⏳ セッション継続と判定されました")
                return "INCOMPLETE"

        except Exception as e:
            print(f"❌ 完了判定エラー: {e}")
            import traceback
            traceback.print_exc()
            return f"完了判定中にエラーが発生しました: {str(e)}"

# ADK用のエクスポート関数
def hera_session_agent(api_key: str | None = None):
    """Heraセッションエージェントのファクトリ関数

    ADK Web UIから呼び出される関数
    """
    return ADKHeraAgent()
