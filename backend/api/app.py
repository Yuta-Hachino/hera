import os
import uuid
import json
import asyncio
import threading
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

load_dotenv()

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
CORS(app)

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

    return jsonify({
        'message': '収集が完了しました。ありがとうございました。',
        'user_profile': profile_pruned,
        'conversation_history': history,
        'information_progress': progress,
        'missing_fields': [],
        'information_complete': True
    })

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
    app.run(debug=True, port=8080)
