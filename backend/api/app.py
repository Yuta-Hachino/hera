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
    # ディレクトリが存在しない場合は作成
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ensure_adk_session(app_name: str, user_id: str, session_id: str, base_url: str):
    """ADKセッションが存在するか確認し、存在しない場合は作成する"""
    try:
        # 既存確認
        print(f"[DEBUG] セッション確認: {base_url}/apps/{app_name}/users/{user_id}/sessions/{session_id}")
        r = requests.get(f"{base_url}/apps/{app_name}/users/{user_id}/sessions/{session_id}", timeout=1000)
        print(f"[DEBUG] セッション確認結果: {r.status_code}")
        if r.status_code == 200:
            print(f"[DEBUG] セッション存在")
            return True
        if r.status_code == 404:
            # 明示 ID で作成
            print(f"[DEBUG] セッション作成: {base_url}/apps/{app_name}/users/{user_id}/sessions/{session_id}")
            r2 = requests.post(
                f"{base_url}/apps/{app_name}/users/{user_id}/sessions/{session_id}",
                json={}, timeout=1000
            )
            print(f"[DEBUG] セッション作成結果: {r2.status_code}")
            result = r2.status_code in (200, 201)
            print(f"[DEBUG] セッション作成成功: {result}")
            return result
        # それ以外はエラー
        print(f"[DEBUG] セッション確認エラー: {r.status_code}")
        r.raise_for_status()
        return False
    except Exception as e:
        print(f"ADKセッション確認エラー: {e}")
        return False

def call_hera_agent(session_id: str, message: str):
    """ADK Web UIサーバー経由でHeraエージェントにメッセージを送信"""
    try:
        # ADK Web UIサーバーの正しいエンドポイントを使用
        # セッション管理は自動的に処理されるため、直接/runエンドポイントを呼び出し
        print(f"[DEBUG] /run呼び出し開始: session_id={session_id}, message={message}")
        message_response = requests.post(
            f"{ADK_BASE_URL}/run",
            json={
                "app_name": "hera",
                "user_id": "user",
                "session_id": session_id,
                "new_message": {
                    "role": "user",
                    "parts": [{"text": message}]
                }
            },
            timeout=1000
        )
        print(f"[DEBUG] /run呼び出し完了: status_code={message_response.status_code}")

        if message_response.status_code not in [200, 201]:
            print(f"ADK Web UI通信エラー: {message_response.status_code}")
            print(f"エラーレスポンス: {message_response.text}")
            return {
                "error": "エージェントサーバーとの通信に失敗しました",
                "message": "申し訳ございません。しばらく時間をおいてから再度お試しください。"
            }

        # レスポンスデータを取得
        response_data = message_response.json()

        # レスポンスがリストの場合（イベントの配列）
        if isinstance(response_data, list):
            events = response_data
            # イベントからエージェントの応答を抽出
            agent_messages = []
            for event in events:
                # content.parts[].textを抽出
                if 'content' in event and 'parts' in event['content']:
                    for part in event['content']['parts']:
                        if 'text' in part:
                            agent_messages.append(part['text'])
                        # functionResponseからもテキストを抽出
                        elif 'functionResponse' in part and 'response' in part['functionResponse']:
                            response_data = part['functionResponse']['response']
                            if 'result' in response_data:
                                try:
                                    result = json.loads(response_data['result'])
                                    if 'message' in result:
                                        agent_messages.append(result['message'])
                                except:
                                    pass

            # 最新のエージェント応答を取得
            agent_response = agent_messages[-1] if agent_messages else "申し訳ございません。応答を取得できませんでした。"

            return {
                "message": agent_response,
                "user_profile": {},
                "conversation_history": events,
                "information_progress": {}
            }
        else:
            # レスポンスが辞書の場合
            events = response_data.get('events', [])
            agent_messages = []

            for event in events:
                if event.get('type') == 'agent_response':
                    agent_messages.append(event.get('text', ''))
                elif 'text' in event:
                    agent_messages.append(event['text'])

            # 最新のエージェント応答を取得
            agent_response = agent_messages[0] if agent_messages else "申し訳ございません。応答を取得できませんでした。"

            # セッション状態からプロファイル情報を抽出
            user_profile = response_data.get('user_profile', {})

            return {
                "message": agent_response,
                "user_profile": user_profile,
                "conversation_history": events,
                "information_progress": {}
            }

    except requests.exceptions.Timeout as e:
        print(f"[DEBUG] ADK Web UIタイムアウト: {e}")
        print(f"[DEBUG] タイムアウト時間: 1000秒")
        return {
            "error": "エージェントサーバーとの通信がタイムアウトしました",
            "message": "申し訳ございません。しばらく時間をおいてから再度お試しください。"
        }
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] ADK Web UI通信エラー: {type(e).__name__}: {e}")
        return {
            "error": "エージェントサーバーとの通信に失敗しました",
            "message": "申し訳ございません。しばらく時間をおいてから再度お試しください。"
        }
    except Exception as e:
        print(f"[DEBUG] エージェント処理エラー: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
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

    # ✅ ADKセッションを先に作る/確認する
    ok = ensure_adk_session(app_name="hera", user_id="user",
                            session_id=session_id, base_url=ADK_BASE_URL)
    if not ok:
        return jsonify({'error': 'ADKセッションの作成/確認に失敗しました'}), 502

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
@app.route('/api/sessions/<session_id>/statfus', methods=['GET'])
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
            timeout=1000
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