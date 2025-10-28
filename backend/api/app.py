import os
import uuid
import json
import asyncio
import threading
from types import SimpleNamespace
from typing import Any, Dict, List, Optional
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import get_sessions_dir
from werkzeug.utils import secure_filename
from flask import send_from_directory
from agents.hera.adk_hera_agent import ADKHeraAgent
from agents.hera.profile_validation import (
    build_information_progress,
    compute_missing_fields,
    profile_is_complete,
    prune_empty_fields,
)
from agents.family.persona_generator import PersonaGenerator
from agents.family.tooling import FamilyToolSet
from agents.family.story_generator import StoryGenerator
from agents.family.letter_generator import LetterGenerator
from utils.logger import setup_logger
from utils.env_validator import validate_env

# 環境変数を読み込み
load_dotenv()

# 環境変数の検証
try:
    validate_env()
except Exception as e:
    print(f"\n{e}\n")
    sys.exit(1)

# ロガーの設定
logger = setup_logger(__name__, log_file='logs/app.log')
logger.info("アプリケーション起動")

# Heraエージェントを直接初期化し、非同期ループを常駐させる
hera_agent = ADKHeraAgent(
    gemini_api_key=os.getenv("GEMINI_API_KEY")
)
_agent_loop = asyncio.new_event_loop()


def _agent_loop_worker() -> None:
    asyncio.set_event_loop(_agent_loop)
    _agent_loop.run_forever()


threading.Thread(target=_agent_loop_worker, daemon=True).start()


def run_async(coro):
    """バックグラウンドループ上でコルーチンを同期的に実行"""
    future = asyncio.run_coroutine_threadsafe(coro, _agent_loop)
    try:
        return future.result()
    except Exception:
        future.cancel()
        raise

# Flaskアプリ
app = Flask(__name__)

# CORS設定（環境変数で許可オリジンを制御）
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
CORS(app, origins=allowed_origins, supports_credentials=True)
logger.info(f"CORS許可オリジン: {allowed_origins}")

# セッションディレクトリ
SESSIONS_DIR = get_sessions_dir()
os.makedirs(SESSIONS_DIR, exist_ok=True)

# Utility関数

def session_path(session_id: str) -> str:
    return os.path.join(SESSIONS_DIR, session_id)

def load_file(path: str, default=None):
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return default

def save_file(path: str, data):
    # ディレクトリが存在しない場合は作成
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class FamilyConversationSession:
    """家族エージェントとの対話状態を管理"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.toolset: Optional[FamilyToolSet] = None
        self.personas = []
        self.initialized = False
        self.user_profile: Dict[str, Any] = {}
        self.state: Dict[str, Any] = {
            "family_conversation_log": [],
            "family_trip_info": {},
            "family_plan_prompted": False,
            "family_plan_confirmed": False,
            "family_conversation_complete": False,
            "family_plan_data": None,
            "family_plan_generated": False,
        }
        self.context = SimpleNamespace(state=self.state)
        self._load_cached_state()

    def _load_cached_state(self) -> None:
        """既存の会話ログや旅行情報があれば読み込む"""
        session_dir = session_path(self.session_id)
        conversation_path = os.path.join(session_dir, 'family_conversation.json')
        trip_path = os.path.join(session_dir, 'family_trip_info.json')
        plan_path = os.path.join(session_dir, 'family_plan.json')

        cached_log = load_file(conversation_path, [])
        if isinstance(cached_log, list):
            self.state["family_conversation_log"] = cached_log

        cached_trip = load_file(trip_path, {})
        if isinstance(cached_trip, dict):
            self.state["family_trip_info"] = cached_trip

        cached_plan = load_file(plan_path, None)
        if isinstance(cached_plan, dict):
            self.state["family_plan_data"] = cached_plan
            self.state["family_plan_generated"] = True
            self.state["family_conversation_complete"] = True

    async def initialize(self) -> None:
        """ペルソナ生成とツールセット初期化"""
        if self.initialized:
            return

        profile = load_file(
            os.path.join(session_path(self.session_id), 'user_profile.json'),
            {}
        )
        if not profile:
            raise ValueError("ユーザープロファイルが見つからないため、家族会話を開始できません。")
        self.user_profile = profile

        generator = PersonaGenerator()
        generated = await generator.generate_personas(profile)
        self.personas = generator.build_persona_objects(generated)
        self.toolset = FamilyToolSet(self.personas)
        self.initialized = True

    async def send_message(self, user_message: str) -> List[Dict[str, Any]]:
        """ユーザーメッセージに対して家族メンバーの発話を生成"""
        await self.initialize()

        log = self.state.setdefault("family_conversation_log", [])
        log.append({
            "speaker": "user",
            "message": user_message,
            "timestamp": datetime.now().isoformat()
        })

        responses: List[Dict[str, Any]] = []
        if not self.toolset:
            return responses

        for family_tool in self.toolset.tools:
            try:
                result = await family_tool.tool.func(
                    tool_context=self.context,
                    input_text=user_message,
                )
                if result and result.get("message"):
                    response_timestamp = datetime.now().isoformat()
                    # ツール側で追加された最新ログにタイムスタンプを付与
                    if self.state.get("family_conversation_log"):
                        self.state["family_conversation_log"][-1]["timestamp"] = response_timestamp
                    responses.append({
                        "speaker": result.get("speaker", family_tool.persona.role),
                        "message": result["message"],
                        "timestamp": response_timestamp,
                    })
            except Exception as tool_error:
                fallback_message = (
                    "ごめんなさい、少し調子が悪いみたい。また後で話そうね。"
                    f"（詳細: {tool_error}）"
                )
                error_entry = {
                    "speaker": family_tool.persona.role,
                    "message": fallback_message,
                    "timestamp": datetime.now().isoformat(),
                }
                responses.append(error_entry)
                log.append(error_entry)

        await self._maybe_finalize_plan()

        return responses

    def persist(self) -> None:
        """セッション状態をディスクに保存"""
        session_dir = session_path(self.session_id)
        os.makedirs(session_dir, exist_ok=True)
        save_file(
            os.path.join(session_dir, 'family_conversation.json'),
            self.state.get("family_conversation_log", []),
        )
        save_file(
            os.path.join(session_dir, 'family_trip_info.json'),
            self.state.get("family_trip_info", {}),
        )
        if self.state.get("family_plan_data"):
            save_file(
                os.path.join(session_dir, 'family_plan.json'),
                self.state["family_plan_data"],
            )

    def status(self) -> Dict[str, Any]:
        return {
            "conversation_history": self.state.get("family_conversation_log", []),
            "family_trip_info": self.state.get("family_trip_info", {}),
            "conversation_complete": bool(self.state.get("family_conversation_complete")),
            "family_plan": self.state.get("family_plan_data"),
        }

    async def _maybe_finalize_plan(self) -> None:
        """旅行計画が確定したタイミングでストーリーと手紙を生成"""
        if self.state.get("family_plan_generated"):
            return
        if not self.state.get("family_plan_confirmed"):
            return

        trip_info = self.state.get("family_trip_info") or {}
        destination = trip_info.get("destination")
        activities = trip_info.get("activities", [])
        if not destination or not activities:
            return

        plan_data = await self._generate_family_plan(trip_info)
        if plan_data:
            self.state["family_plan_data"] = plan_data
            self.state["family_plan_generated"] = True
            self.state["family_conversation_complete"] = True
            self.persist()

    async def _generate_family_plan(self, trip_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """ストーリーと手紙を生成して保存"""
        conversation_log = self.state.get("family_conversation_log", [])
        personas = self.toolset.get_personas() if self.toolset else self.personas
        if not personas:
            return None

        try:
            story_generator = StoryGenerator()
            story = await story_generator.generate_story(
                conversation_log=conversation_log,
                trip_info=trip_info,
                personas=personas,
            )
        except Exception as e:
            print(f"[WARN] family story generation failed: {e}")
            story = self._generate_fallback_summary(
                conversation_log,
                trip_info.get("destination"),
                trip_info.get("activities", []),
            )

        try:
            letter_generator = LetterGenerator()
            user_name = self.user_profile.get("name") if isinstance(self.user_profile, dict) else None
            letter = await letter_generator.generate_letter(
                story=story,
                trip_info=trip_info,
                family_members=personas,
                user_name=user_name,
            )
        except Exception as e:
            print(f"[WARN] family letter generation failed: {e}")
            letter = ""

        plan_data = {
            "destination": trip_info.get("destination"),
            "activities": trip_info.get("activities", []),
            "story": story,
            "letter": letter,
            "conversation_log": conversation_log,
        }
        return plan_data

    def _generate_fallback_summary(
        self,
        conversation_log: List[Dict[str, Any]],
        destination: Optional[str],
        activities: List[str],
    ) -> str:
        activities_text = "、".join(activities) if activities else "楽しい時間"
        intro = destination or "ワクワクする場所"
        summary_lines = [
            f"家族みんなで{intro}に向かう計画がまとまりました。",
            "対話の中では、未来のパートナーや子どもたちが期待に胸を膨らませながら、",
            "旅行中にやりたいことや、互いへの気遣いをたくさん語ってくれました。",
            f"特に「{activities_text}」を一緒に楽しみたいという想いが強く表れています。",
            "",
            "家族で過ごすひとときが、きっと温かく忘れられない思い出になるでしょう。",
        ]
        if conversation_log:
            summary_lines.append("")
            summary_lines.append("【会話のハイライト】")
            for item in conversation_log[-3:]:
                speaker = item.get("speaker", "家族")
                message = item.get("message", "")
                summary_lines.append(f"{speaker}: {message}")
        return "\n".join(summary_lines)


FAMILY_SESSIONS: Dict[str, FamilyConversationSession] = {}


def get_family_session(session_id: str) -> FamilyConversationSession:
    session = FAMILY_SESSIONS.get(session_id)
    if session is None:
        session = FamilyConversationSession(session_id)
        FAMILY_SESSIONS[session_id] = session
    return session

 

# 1. セッション新規作成
@app.route('/api/sessions', methods=['POST'])
def create_session():
    session_id = str(uuid.uuid4())
    path = session_path(session_id)
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(path, 'photos'), exist_ok=True)
    # プロファイル初期化
    save_file(os.path.join(path, 'user_profile.json'), {})
    save_file(os.path.join(path, 'conversation_history.json'), [])

    try:
        run_async(hera_agent.start_session(session_id))
    except Exception as e:
        print(f"[WARN] start_session failed for {session_id}: {e}")

    return jsonify({
        'session_id': session_id,
        'created_at': str(uuid.uuid1().time),
        'status': 'created'
    })

# 2. メッセージ送信 & ヒアリング進行
@app.route('/api/sessions/<session_id>/messages', methods=['POST'])
def send_message(session_id):
    req = request.get_json()
    if not req or 'message' not in req:
        return jsonify({'error': 'messageフィールド必須'}), 400

    user_message = req['message']

    session_dir = session_path(session_id)
    os.makedirs(session_dir, exist_ok=True)
    os.makedirs(os.path.join(session_dir, 'photos'), exist_ok=True)

    try:
        raw_response = run_async(
            hera_agent.run(
                message=user_message,
                session_id=session_id,
            )
        )
        if isinstance(raw_response, str):
            agent_response = json.loads(raw_response)
        else:
            agent_response = raw_response
    except Exception as e:
        print(f"[ERROR] Hera agent execution failed: {e}")
        return jsonify({
            'error': 'エージェント処理でエラーが発生しました',
            'reply': '申し訳ございません。しばらく時間をおいてから再度お試しください。'
        }), 500

    # セッションデータの保存
    profile_from_agent = agent_response.get('user_profile') or {}
    profile_pruned = prune_empty_fields(profile_from_agent)
    save_file(os.path.join(session_dir, 'user_profile.json'), profile_pruned)

    history = load_file(os.path.join(session_dir, 'conversation_history.json'), [])
    if not history:
        # fall back to in-memoryログ
        history = hera_agent.conversation_history

    information_progress = agent_response.get('information_progress') or build_information_progress(profile_pruned)
    missing_fields = agent_response.get('missing_fields') or compute_missing_fields(profile_pruned)

    return jsonify({
        'reply': agent_response.get('message', ''),
        'conversation_history': history,
        'user_profile': profile_pruned,
        'information_progress': information_progress,
        'missing_fields': missing_fields,
        'profile_complete': len(missing_fields) == 0,
        'session_status': agent_response.get('session_status'),
        'completion_message': agent_response.get('completion_message'),
        'last_extracted_fields': agent_response.get('last_extracted_fields', {}),
    })

# 3. 進捗・履歴・プロフィール取得
@app.route('/api/sessions/<session_id>/status', methods=['GET'])
def get_status(session_id):
    session_dir = session_path(session_id)
    profile = load_file(os.path.join(session_dir, 'user_profile.json'), {}) or {}
    profile_pruned = prune_empty_fields(profile)
    history = load_file(os.path.join(session_dir, 'conversation_history.json'), []) or []

    progress = build_information_progress(profile_pruned)
    missing_fields = compute_missing_fields(profile_pruned)

    return jsonify({
        'user_profile': profile_pruned,
        'conversation_history': history,
        'information_progress': progress,
        'missing_fields': missing_fields,
        'profile_complete': len(missing_fields) == 0
    })

# 4. セッション完了（必須情報充足/保存・family_agent転送準備）
@app.route('/api/sessions/<session_id>/complete', methods=['POST'])
def complete_session(session_id):
    session_dir = session_path(session_id)
    profile = load_file(os.path.join(session_dir, 'user_profile.json'), {}) or {}
    profile_pruned = prune_empty_fields(profile)
    history = load_file(os.path.join(session_dir, 'conversation_history.json'), []) or []

    progress = build_information_progress(profile_pruned)
    missing_fields = compute_missing_fields(profile_pruned)

    if not profile_is_complete(profile_pruned):
        return jsonify({
            'error': '必須項目が未入力のため、完了できません。',
            'user_profile': profile_pruned,
            'conversation_history': history,
            'information_progress': progress,
            'missing_fields': missing_fields,
            'information_complete': False
        }), 400

    # 家族エージェントの準備を先行実行（ペルソナ生成など）
    try:
        family_session = get_family_session(session_id)
        run_async(family_session.initialize())
    except Exception as e:
        print(f"[WARN] 家族エージェント初期化に失敗しました: {e}")

    return jsonify({
        'message': '収集が完了しました。ありがとうございました。',
        'user_profile': profile_pruned,
        'conversation_history': history,
        'information_progress': progress,
        'missing_fields': [],
        'information_complete': True
    })


# --- 家族エージェント連携API ---
@app.route('/api/sessions/<session_id>/family/status', methods=['GET'])
def get_family_status_api(session_id):
    try:
        session = get_family_session(session_id)
        run_async(session._maybe_finalize_plan())
        session.persist()
        return jsonify(session.status())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/<session_id>/family/messages', methods=['POST'])
def send_family_message(session_id):
    req = request.get_json() or {}
    user_message = req.get('message')
    if not user_message:
        return jsonify({'error': 'messageフィールド必須'}), 400

    session = get_family_session(session_id)
    try:
        replies = run_async(session.send_message(user_message))
        session.persist()
        status = session.status()
        return jsonify({
            'reply': replies,
            'conversation_history': status['conversation_history'],
            'family_trip_info': status['family_trip_info'],
            'conversation_complete': status['conversation_complete'],
            'family_plan': status.get('family_plan'),
        })
    except Exception as e:
        return jsonify({'error': f'家族エージェントとの会話に失敗しました: {e}'}), 500

# ヘルスチェック
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

# --- 画像アップロード/生成API ---
UPLOAD_EXTENSIONS = {'.jpg', '.jpeg', '.png'}

# 1. ユーザー画像アップロード
@app.route('/api/sessions/<session_id>/photos/user', methods=['POST'])
def upload_user_photo(session_id):
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'error': '画像ファイルがありません'}), 400
    file = request.files['file']
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in UPLOAD_EXTENSIONS:
        return jsonify({'status': 'error', 'error': '対応形式: jpg, jpeg, png'}), 400
    dest_dir = os.path.join(session_path(session_id), 'photos')
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, 'user.png')
    file.save(dest_path)
    return jsonify({'status': 'success', 'image_url': f'/api/sessions/{session_id}/photos/user.png'})

# 画像ファイル取得（静的配信用途）
@app.route('/api/sessions/<session_id>/photos/<filename>')
def get_photo(session_id, filename):
    dirpath = os.path.join(session_path(session_id), 'photos')
    return send_from_directory(dirpath, filename)

# 2. パートナー画像生成
@app.route('/api/sessions/<session_id>/generate-image', methods=['POST'])
def generate_partner_image(session_id):
    req = request.get_json() or {}
    target = req.get('target')
    if target != 'partner':
        return jsonify({'status': 'error', 'error': '現在partnerのみ対応'}), 400
    # プロファイルから顔特徴取得
    session_dir = session_path(session_id)
    prof = load_file(os.path.join(session_dir, 'user_profile.json'), {})
    desc = prof.get('partner_face_description')
    if not desc:
        return jsonify({'status': 'error', 'error': 'partner_face_descriptionが未入力'}), 400
    prompt = f"パートナーの顔の特徴: {desc}"
    try:
        from google.generativeai import GenerativeModel
        gm = GenerativeModel('gemini-2.5-pro')
        # 仮: 本来は画像生成APIを使う（ここはプロンプトをtextのままダミー画像返すスタブ）
        # 実際は gm.generate_image(prompt=...) などを記載
        # 今はダミー生成(JPEG白紙画像)
        from PIL import Image
        img = Image.new('RGB', (512, 512), color='white')
        dest_dir = os.path.join(session_dir, 'photos')
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, 'partner.png')
        img.save(dest_path)
        return jsonify({'status': 'success', 'image_url': f'/api/sessions/{session_id}/photos/partner.png', 'meta': {'target': 'partner', 'prompt_used': prompt}})
    except Exception as e:
        return jsonify({'status': 'error', 'error': f'Gemini API error: {e}'})

# 3. 子ども画像 合成API（スタブ）
@app.route('/api/sessions/<session_id>/generate-child-image', methods=['POST'])
def generate_child_image(session_id):
    session_dir = session_path(session_id)
    img_user = os.path.join(session_dir, 'photos', 'user.png')
    img_partner = os.path.join(session_dir, 'photos', 'partner.png')
    if not (os.path.exists(img_user) and os.path.exists(img_partner)):
        return jsonify({'status': 'error', 'error': 'user/partner画像が両方必要'}), 400
    # 子ども画像は現状ダミー生成(白)→本番は合成APIやGAN画像生成等に拡張
    from PIL import Image
    img = Image.new('RGB', (512, 512), color='white')
    dest_path = os.path.join(session_dir, 'photos', 'child_1.png')
    img.save(dest_path)
    return jsonify({'status': 'success', 'image_url': f'/api/sessions/{session_id}/photos/child_1.png', 'meta': {'target': 'child', 'child_ver': 1}})

if __name__ == "__main__":
    # 環境変数でデバッグモードを制御（本番環境では無効化）
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
    port = int(os.getenv('PORT', '8080'))
    app.run(debug=debug_mode, port=port, host='0.0.0.0')
