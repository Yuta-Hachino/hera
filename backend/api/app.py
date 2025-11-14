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
from utils.session_manager import get_session_manager, SessionManager
from utils.storage_manager import create_storage_manager, StorageManager
from utils.auth_middleware import require_auth, optional_auth
from api.firebase_config import initialize_firebase

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

# Firebase Admin SDKを初期化
logger.info("Firebase Admin SDK初期化中...")
initialize_firebase()
logger.info("Firebase Admin SDK初期化完了")

# 非同期ループの準備
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

# セッションディレクトリ（画像保存用に残す）
SESSIONS_DIR = get_sessions_dir()
os.makedirs(SESSIONS_DIR, exist_ok=True)

# セッション管理とストレージ管理の初期化
try:
    session_mgr: SessionManager = get_session_manager()
    storage_mgr: StorageManager = create_storage_manager()
    storage_mode = os.getenv('STORAGE_MODE', 'local').lower()
    logger.info(f"セッション管理初期化完了: {type(session_mgr).__name__}")
    logger.info(f"ストレージ管理初期化完了: {type(storage_mgr).__name__} (mode={storage_mode})")
except Exception as e:
    logger.error(f"マネージャー初期化エラー: {e}")
    raise

# Heraエージェントを初期化（session_managerを渡す）
hera_agent = ADKHeraAgent(
    gemini_api_key=os.getenv("GEMINI_API_KEY"),
    session_manager=session_mgr
)
logger.info("ADK Heraエージェント初期化完了")

# Utility関数

def session_path(session_id: str) -> str:
    """画像保存用のパス取得（後方互換性のため残す）"""
    return os.path.join(SESSIONS_DIR, session_id)

def load_file(path: str, default=None):
    """ファイルベースのデータ読み込み（後方互換性のため残す）"""
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return default

def save_file(path: str, data):
    """ファイルベースのデータ保存（後方互換性のため残す）"""
    # ディレクトリが存在しない場合は作成
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 新しいセッション管理関数
def save_session_data(session_id: str, key: str, data: Any) -> None:
    """セッションデータを保存（Redis/File自動切り替え）"""
    try:
        # session_mgrはDict形式を期待しているので、keyをディクショナリに包む
        session_mgr.save(session_id, {key: data})
        logger.debug(f"セッションデータ保存: {session_id}/{key}")
    except Exception as e:
        logger.error(f"セッションデータ保存エラー: {session_id}/{key} - {e}")
        raise


def load_session_data(session_id: str, key: str, default: Any = None) -> Any:
    """セッションデータを読み込み（Redis/File自動切り替え）"""
    try:
        data = session_mgr.load(session_id)
        if data and key in data:
            logger.debug(f"セッションデータ読み込み: {session_id}/{key}")
            return data[key]
        return default
    except Exception as e:
        logger.error(f"セッションデータ読み込みエラー: {session_id}/{key} - {e}")
        return default


def session_exists(session_id: str) -> bool:
    """セッションが存在するか確認"""
    try:
        return session_mgr.exists(session_id)
    except Exception as e:
        logger.error(f"セッション存在確認エラー: {session_id} - {e}")
        return False


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
        """既存の会話ログや旅行情報があれば読み込む（session_mgr使用）"""
        cached_log = load_session_data(self.session_id, 'family_conversation', [])
        if isinstance(cached_log, list):
            self.state["family_conversation_log"] = cached_log

        cached_trip = load_session_data(self.session_id, 'family_trip_info', {})
        if isinstance(cached_trip, dict):
            self.state["family_trip_info"] = cached_trip

        cached_plan = load_session_data(self.session_id, 'family_plan', None)
        if isinstance(cached_plan, dict):
            self.state["family_plan_data"] = cached_plan
            self.state["family_plan_generated"] = True
            self.state["family_conversation_complete"] = True

    async def initialize(self) -> None:
        """ペルソナ生成とツールセット初期化（session_mgr使用）"""
        if self.initialized:
            return

        profile = load_session_data(self.session_id, 'user_profile', {})
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
        """セッション状態を保存（session_mgr使用）"""
        save_session_data(
            self.session_id,
            'family_conversation',
            self.state.get("family_conversation_log", [])
        )
        save_session_data(
            self.session_id,
            'family_trip_info',
            self.state.get("family_trip_info", {})
        )
        if self.state.get("family_plan_data"):
            save_session_data(
                self.session_id,
                'family_plan',
                self.state["family_plan_data"]
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
@optional_auth
def create_session():
    session_id = str(uuid.uuid4())
    user_id = getattr(request, 'user_id', None)  # JWTから取得（オプション）

    # セッション初期化（session_mgr使用）
    try:
        save_session_data(session_id, 'user_profile', {})
        save_session_data(session_id, 'conversation_history', [])
        save_session_data(session_id, 'created_at', datetime.now().isoformat())

        # Firebase使用時: user_idをセッションに設定
        if user_id:
            save_session_data(session_id, 'user_id', user_id)
            logger.info(f"セッション作成（user_id={user_id}）: {session_id}")
        else:
            logger.info(f"セッション作成（ゲストモード）: {session_id}")
    except Exception as e:
        logger.error(f"セッション作成エラー: {session_id} - {e}")
        return jsonify({'error': 'セッション作成に失敗しました'}), 500

    # 画像保存用ディレクトリ作成（ローカルファイルシステム用）
    path = session_path(session_id)
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(path, 'photos'), exist_ok=True)

    try:
        run_async(hera_agent.start_session(session_id))
    except Exception as e:
        logger.warning(f"start_session failed for {session_id}: {e}")

    return jsonify({
        'session_id': session_id,
        'created_at': datetime.now().isoformat(),
        'status': 'created'
    })

# 2. メッセージ送信 & ヒアリング進行
@app.route('/api/sessions/<session_id>/messages', methods=['POST'])
@optional_auth
def send_message(session_id):
    req = request.get_json()
    if not req or 'message' not in req:
        return jsonify({'error': 'messageフィールド必須'}), 400

    user_message = req['message']

    # セッション存在確認
    if not session_exists(session_id):
        logger.warning(f"存在しないセッション: {session_id}")
        return jsonify({'error': 'セッションが存在しません'}), 404

    # 画像保存用ディレクトリ作成（必要に応じて）
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
        logger.error(f"Hera agent execution failed: {e}")
        return jsonify({
            'error': 'エージェント処理でエラーが発生しました',
            'reply': '申し訳ございません。しばらく時間をおいてから再度お試しください。'
        }), 500

    # セッションデータの保存（session_mgr使用）
    profile_from_agent = agent_response.get('user_profile') or {}
    profile_pruned = prune_empty_fields(profile_from_agent)
    save_session_data(session_id, 'user_profile', profile_pruned)

    history = load_session_data(session_id, 'conversation_history', [])
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
@optional_auth
def get_status(session_id):
    # セッション存在確認
    if not session_exists(session_id):
        logger.warning(f"存在しないセッション: {session_id}")
        return jsonify({'error': 'セッションが存在しません'}), 404

    # session_mgrからデータ取得
    profile = load_session_data(session_id, 'user_profile', {}) or {}
    profile_pruned = prune_empty_fields(profile)
    history = load_session_data(session_id, 'conversation_history', []) or []

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
@optional_auth
def complete_session(session_id):
    # セッション存在確認
    if not session_exists(session_id):
        logger.warning(f"存在しないセッション: {session_id}")
        return jsonify({'error': 'セッションが存在しません'}), 404

    # session_mgrからデータ取得
    profile = load_session_data(session_id, 'user_profile', {}) or {}
    profile_pruned = prune_empty_fields(profile)
    history = load_session_data(session_id, 'conversation_history', []) or []

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
        logger.info(f"家族エージェント初期化完了: {session_id}")
    except Exception as e:
        logger.warning(f"家族エージェント初期化に失敗しました: {e}")

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
@optional_auth
def get_family_status_api(session_id):
    try:
        session = get_family_session(session_id)
        run_async(session._maybe_finalize_plan())
        session.persist()
        return jsonify(session.status())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/<session_id>/family/messages', methods=['POST'])
@optional_auth
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
    # セッション存在確認
    if not session_exists(session_id):
        logger.warning(f"存在しないセッション: {session_id}")
        return jsonify({'status': 'error', 'error': 'セッションが存在しません'}), 404

    if 'file' not in request.files:
        return jsonify({'status': 'error', 'error': '画像ファイルがありません'}), 400

    file = request.files['file']
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in UPLOAD_EXTENSIONS:
        return jsonify({'status': 'error', 'error': '対応形式: jpg, jpeg, png'}), 400

    try:
        # 画像データ読み込み
        file_data = file.read()

        # storage_mgrで保存（ローカル/クラウド自動切り替え）
        image_url = storage_mgr.save_file(session_id, 'photos/user.png', file_data)
        logger.info(f"画像アップロード成功: {session_id}/photos/user.png")

        return jsonify({
            'status': 'success',
            'image_url': image_url
        })
    except Exception as e:
        logger.error(f"画像アップロードエラー: {session_id} - {e}")
        return jsonify({'status': 'error', 'error': '画像の保存に失敗しました'}), 500

# 画像ファイル取得（静的配信用途）
@app.route('/api/sessions/<session_id>/photos/<filename>')
def get_photo(session_id, filename):
    # セッション存在確認
    if not session_exists(session_id):
        logger.warning(f"存在しないセッション: {session_id}")
        return jsonify({'error': 'セッションが存在しません'}), 404

    try:
        # storage_mgrから画像データ取得
        file_data = storage_mgr.load_file(session_id, f'photos/{filename}')

        if file_data is None:
            logger.warning(f"画像が見つかりません: {session_id}/photos/{filename}")
            return jsonify({'error': '画像が見つかりません'}), 404

        # Content-Typeを推測
        import mimetypes
        content_type, _ = mimetypes.guess_type(filename)
        if content_type is None:
            content_type = 'application/octet-stream'

        # バイナリデータをレスポンス
        from flask import Response
        return Response(file_data, mimetype=content_type)

    except Exception as e:
        logger.error(f"画像取得エラー: {session_id}/photos/{filename} - {e}")
        return jsonify({'error': '画像の取得に失敗しました'}), 500

# 2. パートナー画像生成
@app.route('/api/sessions/<session_id>/generate-image', methods=['POST'])
def generate_partner_image(session_id):
    # セッション存在確認
    if not session_exists(session_id):
        logger.warning(f"存在しないセッション: {session_id}")
        return jsonify({'status': 'error', 'error': 'セッションが存在しません'}), 404

    req = request.get_json() or {}
    target = req.get('target')
    if target != 'partner':
        return jsonify({'status': 'error', 'error': '現在partnerのみ対応'}), 400

    # プロファイルから顔特徴取得（session_mgr使用）
    prof = load_session_data(session_id, 'user_profile', {})
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
        import io
        img = Image.new('RGB', (512, 512), color='white')

        # 画像をバイトデータに変換
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_data = img_bytes.getvalue()

        # storage_mgrで保存（ローカル/クラウド自動切り替え）
        image_url = storage_mgr.save_file(session_id, 'photos/partner.png', img_data)
        logger.info(f"パートナー画像生成成功: {session_id}/photos/partner.png")

        return jsonify({
            'status': 'success',
            'image_url': image_url,
            'meta': {'target': 'partner', 'prompt_used': prompt}
        })
    except Exception as e:
        logger.error(f"パートナー画像生成エラー: {session_id} - {e}")
        return jsonify({'status': 'error', 'error': f'画像生成に失敗しました: {e}'}), 500

# 3. 子ども画像 合成API（スタブ）
@app.route('/api/sessions/<session_id>/generate-child-image', methods=['POST'])
def generate_child_image(session_id):
    # セッション存在確認
    if not session_exists(session_id):
        logger.warning(f"存在しないセッション: {session_id}")
        return jsonify({'status': 'error', 'error': 'セッションが存在しません'}), 404

    try:
        # storage_mgrから画像データ取得
        img_user_data = storage_mgr.load_file(session_id, 'photos/user.png')
        img_partner_data = storage_mgr.load_file(session_id, 'photos/partner.png')

        if img_user_data is None or img_partner_data is None:
            return jsonify({
                'status': 'error',
                'error': 'user/partner画像が両方必要です'
            }), 400

        # 子ども画像は現状ダミー生成(白)→本番は合成APIやGAN画像生成等に拡張
        from PIL import Image
        import io
        img = Image.new('RGB', (512, 512), color='white')

        # 画像をバイトデータに変換
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_data = img_bytes.getvalue()

        # storage_mgrで保存（ローカル/クラウド自動切り替え）
        image_url = storage_mgr.save_file(session_id, 'photos/child_1.png', img_data)
        logger.info(f"子供画像生成成功: {session_id}/photos/child_1.png")

        return jsonify({
            'status': 'success',
            'image_url': image_url,
            'meta': {'target': 'child', 'child_ver': 1}
        })
    except Exception as e:
        logger.error(f"子供画像生成エラー: {session_id} - {e}")
        return jsonify({'status': 'error', 'error': f'画像生成に失敗しました: {e}'}), 500


# ============================================================
# 🆕 Gemini Live API 統合エンドポイント（新機能）
# ============================================================
# Live API機能は環境変数 GEMINI_LIVE_MODE で制御
# デフォルト: disabled（既存機能を保護）

LIVE_API_ENABLED = os.getenv('GEMINI_LIVE_MODE', 'disabled').lower() == 'enabled'

if LIVE_API_ENABLED:
    try:
        from utils.ephemeral_token_manager import get_ephemeral_token_manager
        ephemeral_token_mgr = get_ephemeral_token_manager()
        logger.info("✅ Gemini Live API機能: 有効")
    except Exception as e:
        logger.warning(f"⚠️ Live API初期化失敗: {e}")
        LIVE_API_ENABLED = False
else:
    logger.info("ℹ️ Gemini Live API機能: 無効（既存機能のみ）")


@app.route('/api/sessions/<session_id>/ephemeral-token', methods=['POST'])
@optional_auth
def create_ephemeral_token(session_id):
    """
    Gemini Live API用のEphemeralトークンを生成（新機能）

    Live API機能が無効の場合は503エラーを返します。
    セッションが存在しない場合は404エラーを返します。

    Returns:
        200: トークン生成成功
        404: セッションが存在しない
        500: トークン生成失敗
        503: Live API機能が無効
    """
    # Live API機能チェック
    if not LIVE_API_ENABLED:
        logger.warning(f"Live API機能が無効です（セッション: {session_id}）")
        return jsonify({
            'status': 'error',
            'error': 'Gemini Live API機能が無効です',
            'message': 'GEMINI_LIVE_MODE=enabled を設定してください'
        }), 503

    # セッション存在確認
    if not session_exists(session_id):
        logger.warning(f"存在しないセッション: {session_id}")
        return jsonify({
            'status': 'error',
            'error': 'セッションが存在しません'
        }), 404

    try:
        # モデル名取得
        model = os.getenv('GEMINI_LIVE_MODEL', 'gemini-2.0-flash-live-preview-04-09')

        # Ephemeralトークン生成
        logger.info(f"🔑 Ephemeralトークン生成開始: session={session_id}, model={model}")
        token_data = ephemeral_token_mgr.create_token(model=model)

        # WebSocket URL生成
        ws_endpoint = ephemeral_token_mgr.get_websocket_url(token_data['token'])

        logger.info(f"✅ Ephemeralトークン生成成功: session={session_id}")

        return jsonify({
            'status': 'success',
            'token': token_data['token'],
            'expire_time': token_data['expire_time'].isoformat(),
            'model': model,
            'ws_endpoint': ws_endpoint,
            'audio_config': {
                'input_enabled': os.getenv('AUDIO_INPUT_ENABLED', 'false').lower() == 'true',
                'input_sample_rate': int(os.getenv('AUDIO_INPUT_SAMPLE_RATE', '16000')),
                'output_sample_rate': int(os.getenv('AUDIO_OUTPUT_SAMPLE_RATE', '24000')),
                'chunk_size_ms': int(os.getenv('AUDIO_CHUNK_SIZE_MS', '100'))
            }
        })

    except Exception as e:
        logger.error(f"❌ Ephemeralトークン生成エラー: session={session_id} - {e}")
        return jsonify({
            'status': 'error',
            'error': 'トークン生成に失敗しました',
            'message': str(e)
        }), 500


if __name__ == "__main__":
    # 環境変数でデバッグモードを制御（本番環境では無効化）
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
    port = int(os.getenv('PORT', '8080'))
    app.run(debug=debug_mode, port=port, host='0.0.0.0')
