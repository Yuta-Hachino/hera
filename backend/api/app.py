import os
import uuid
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import BaseModel
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import get_sessions_dir
from agents.hera.adk_hera_agent import ADKHeraAgent
import asyncio
from werkzeug.utils import secure_filename
from flask import send_from_directory

load_dotenv() 

# Flaskアプリ
app = Flask(__name__)
CORS(app)

# セッションディレクトリ
SESSIONS_DIR = get_sessions_dir()
os.makedirs(SESSIONS_DIR, exist_ok=True)

hera_agent_map = {}  # セッションIDごとにAIエージェントインスタンスをメモリ管理

class MessageRequest(BaseModel):
    message: str

# Utility関数

def session_path(session_id: str) -> str:
    return os.path.join(SESSIONS_DIR, session_id)

def load_file(path: str, default=None):
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return default

def save_file(path: str, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 1. セッション新規作成
@app.route('/api/sessions', methods=['POST'])
def create_session():
    session_id = str(uuid.uuid4())
    path = session_path(session_id)
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(path, 'photos'), exist_ok=True)
    # Heraエージェント準備
    hera_agent_map[session_id] = ADKHeraAgent(gemini_api_key=os.environ.get('GEMINI_API_KEY'))
    # プロファイル初期化
    save_file(os.path.join(path, 'user_profile.json'), {})
    save_file(os.path.join(path, 'conversation_history.json'), [])
    return jsonify({
        'session_id': session_id,
        'created_at': uuid.uuid1().ctime() if hasattr(uuid.uuid1(), 'ctime') else '',
        'status': 'created'
    })

# 2. メッセージ送信 & ヒアリング進行
@app.route('/api/sessions/<session_id>/messages', methods=['POST'])
def send_message(session_id):
    req = request.get_json()
    if not req or 'message' not in req:
        return jsonify({'error': 'messageフィールド必須'}), 400
    user_message = req['message']

    # エージェント確保
    if session_id not in hera_agent_map:
        hera_agent_map[session_id] = ADKHeraAgent(gemini_api_key=os.environ.get('GEMINI_API_KEY'))
    agent = hera_agent_map[session_id]
    # セッション同期
    asyncio.run(agent.start_session(session_id))

    # ADKで応答生成
    response_json = asyncio.run(agent.extract_user_info(user_message))
    response = json.loads(response_json) if isinstance(response_json, str) else response_json

    # 履歴・プロファイルをディスクにも保存
    session_dir = session_path(session_id)
    save_file(os.path.join(session_dir, 'user_profile.json'), agent.user_profile.dict())
    save_file(os.path.join(session_dir, 'conversation_history.json'), agent.conversation_history)

    # 必要に応じて進捗も返す
    progress = agent._check_information_progress() if hasattr(agent, '_check_information_progress') else {}
    return jsonify({
        'reply': response.get('message', ''),
        'conversation_history': agent.conversation_history,
        'user_profile': agent.user_profile.dict(),
        'information_progress': progress
    })

# 3. 進捗・履歴・プロフィール取得
@app.route('/api/sessions/<session_id>/status', methods=['GET'])
def get_status(session_id):
    session_dir = session_path(session_id)
    profile = load_file(os.path.join(session_dir, 'user_profile.json'), {})
    history = load_file(os.path.join(session_dir, 'conversation_history.json'), [])
    # エージェント優先で進捗も返す
    agent = hera_agent_map.get(session_id)
    progress = agent._check_information_progress() if agent and hasattr(agent, '_check_information_progress') else {}
    return jsonify({
        'user_profile': profile,
        'conversation_history': history,
        'information_progress': progress
    })

# 4. セッション完了（必須情報充足/保存・family_agent転送準備）
@app.route('/api/sessions/<session_id>/complete', methods=['POST'])
def complete_session(session_id):
    agent = hera_agent_map.get(session_id)
    if not agent:
        return jsonify({'error': 'セッションが見つかりません'}), 404
    # 完了判定＆データ保存
    message = ''
    try:
        # 空のメッセージで完了判定
        result = asyncio.run(agent.check_session_completion(""))
        # プロファイル等最新保存
        session_dir = session_path(session_id)
        save_file(os.path.join(session_dir, 'user_profile.json'), agent.user_profile.dict())
        save_file(os.path.join(session_dir, 'conversation_history.json'), agent.conversation_history)
        message = result if result else "収集が完了しました。ありがとうございました。"
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    is_complete = agent.is_information_complete() if hasattr(agent, 'is_information_complete') else False
    return jsonify({
        'message': message,
        'user_profile': agent.user_profile.dict() if hasattr(agent, 'user_profile') else {},
        'information_complete': is_complete
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