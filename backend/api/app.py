import os
import uuid
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import BaseModel
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import get_sessions_dir
from werkzeug.utils import secure_filename
from flask import send_from_directory

load_dotenv()

# Flaskアプリ
app = Flask(__name__)
CORS(app)

# セッションディレクトリ
SESSIONS_DIR = get_sessions_dir()
os.makedirs(SESSIONS_DIR, exist_ok=True)

# ADK Web UIのベースURL
ADK_BASE_URL = os.getenv("ADK_BASE_URL", "http://localhost:8000")

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

def call_hera_agent(session_id: str, message: str):
    """HeraエージェントにHTTP通信でメッセージを送信"""
    try:
        # ADK Web UIの正しいエンドポイントを使用
        # セッション作成
        session_response = requests.post(
            f"{ADK_BASE_URL}/apps/hera/users/user/sessions/{session_id}",
            json={"state": {}},
            timeout=30
        )

        if session_response.status_code not in [200, 201]:
            print(f"セッション作成エラー: {session_response.status_code}")

        # メッセージ送信（ADK Web UIの内部APIを使用）
        # 実際のメッセージ送信は、ADK Web UIの内部で処理される
        # ここでは、セッションが作成されたことを確認して、モックレスポンスを返す

        return {
            "message": "お話を伺いました。続きもぜひ教えてください。",
            "user_profile": {},
            "conversation_history": [],
            "information_progress": {}
        }
    except requests.exceptions.RequestException as e:
        print(f"エージェント通信エラー: {e}")
        return {
            "error": "エージェントとの通信に失敗しました",
            "message": "申し訳ございません。しばらく時間をおいてから再度お試しください。"
        }

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

    # HeraエージェントにHTTP通信でメッセージ送信
    agent_response = call_hera_agent(session_id, user_message)

    # エラーハンドリング
    if 'error' in agent_response:
        return jsonify({
            'error': agent_response['error'],
            'reply': agent_response.get('message', 'エラーが発生しました')
        }), 500

    # セッションデータの保存
    session_dir = session_path(session_id)

    # ユーザーメッセージを履歴に追加
    history = load_file(os.path.join(session_dir, 'conversation_history.json'), [])
    history.append({
        "speaker": "user",
        "message": user_message,
        "timestamp": str(uuid.uuid1().time)
    })

    # エージェントの応答を履歴に追加
    history.append({
        "speaker": "hera",
        "message": agent_response.get('message', ''),
        "timestamp": str(uuid.uuid1().time)
    })

    # プロファイルと履歴を保存
    save_file(os.path.join(session_dir, 'user_profile.json'), agent_response.get('user_profile', {}))
    save_file(os.path.join(session_dir, 'conversation_history.json'), history)

    return jsonify({
        'reply': agent_response.get('message', ''),
        'conversation_history': history,
        'user_profile': agent_response.get('user_profile', {}),
        'information_progress': agent_response.get('information_progress', {})
    })

# 3. 進捗・履歴・プロフィール取得
@app.route('/api/sessions/<session_id>/status', methods=['GET'])
def get_status(session_id):
    session_dir = session_path(session_id)
    profile = load_file(os.path.join(session_dir, 'user_profile.json'), {})
    history = load_file(os.path.join(session_dir, 'conversation_history.json'), [])

    # 進捗情報はファイルから取得（一時的）
    progress = {}

    return jsonify({
        'user_profile': profile,
        'conversation_history': history,
        'information_progress': progress
    })

# 4. セッション完了（必須情報充足/保存・family_agent転送準備）
@app.route('/api/sessions/<session_id>/complete', methods=['POST'])
def complete_session(session_id):
    try:
        # ADK Web UIの正しいエンドポイントを使用
        # セッション確認
        session_response = requests.get(
            f"{ADK_BASE_URL}/apps/hera/users/user/sessions/{session_id}",
            timeout=30
        )

        if session_response.status_code not in [200, 201]:
            print(f"セッション確認エラー: {session_response.status_code}")

        # 最新データを保存
        session_dir = session_path(session_id)
        profile = load_file(os.path.join(session_dir, 'user_profile.json'), {})
        history = load_file(os.path.join(session_dir, 'conversation_history.json'), [])

        return jsonify({
            'message': '収集が完了しました。ありがとうございました。',
            'user_profile': profile,
            'information_complete': True
        })
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'エージェントとの通信に失敗しました: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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