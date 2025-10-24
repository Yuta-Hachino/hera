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

if __name__ == "__main__":
    app.run(debug=True, port=8080)