"""
簡単なAPIテスト用サーバー
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import json
import os

app = Flask(__name__)
CORS(app)

# セッション管理（メモリ内）
sessions = {}

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/sessions', methods=['POST'])
def create_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        'user_profile': {},
        'conversation_history': [],
        'information_progress': {}
    }
    return jsonify({
        'session_id': session_id,
        'created_at': '2025-01-21T10:00:00Z',
        'status': 'created'
    })

@app.route('/api/sessions/<session_id>/messages', methods=['POST'])
def send_message(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'セッションが見つかりません'}), 404
    
    req = request.get_json()
    if not req or 'message' not in req:
        return jsonify({'error': 'messageフィールド必須'}), 400
    
    user_message = req['message']
    
    # ダミーレスポンス
    reply = f"こんにちは！{user_message}について教えていただきありがとうございます。"
    
    # 履歴に追加
    sessions[session_id]['conversation_history'].append({
        'speaker': 'user',
        'message': user_message,
        'timestamp': '2025-01-21T10:00:00Z'
    })
    sessions[session_id]['conversation_history'].append({
        'speaker': 'hera',
        'message': reply,
        'timestamp': '2025-01-21T10:00:00Z'
    })
    
    return jsonify({
        'reply': reply,
        'conversation_history': sessions[session_id]['conversation_history'],
        'user_profile': sessions[session_id]['user_profile'],
        'information_progress': sessions[session_id]['information_progress']
    })

@app.route('/api/sessions/<session_id>/status', methods=['GET'])
def get_status(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'セッションが見つかりません'}), 404
    
    return jsonify({
        'user_profile': sessions[session_id]['user_profile'],
        'conversation_history': sessions[session_id]['conversation_history'],
        'information_progress': sessions[session_id]['information_progress']
    })

@app.route('/api/sessions/<session_id>/complete', methods=['POST'])
def complete_session(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'セッションが見つかりません'}), 404
    
    return jsonify({
        'message': '収集が完了しました。ありがとうございました。',
        'user_profile': sessions[session_id]['user_profile'],
        'information_complete': True
    })

if __name__ == "__main__":
    print("テストAPIサーバー起動中...")
    app.run(debug=True, port=8080)

