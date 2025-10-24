import requests
import os

BASE = "http://localhost:8080/api"
DIR = os.path.dirname(__file__)

# 1. セッション作成
def create_session():
    r = requests.post(f"{BASE}/sessions")
    print('セッション作成:', r.status_code, r.json())
    return r.json()['session_id']

# 2. ユーザー画像アップロード
def upload_user_image(session_id):
    img_path = os.path.join(DIR, 'dummy_user.png')
    # 画像がなければ白紙作成
    if not os.path.exists(img_path):
        from PIL import Image
        img = Image.new('RGB', (256,256), 'gray')
        img.save(img_path)
    with open(img_path, 'rb') as f:
        files = {'file': f}
        r = requests.post(f"{BASE}/sessions/{session_id}/photos/user", files=files)
    print('ユーザー画像upload:', r.status_code, r.json())
    return r.json()

# 3. パートナー画像生成API
def generate_partner_image(session_id):
    # ダミーでprofileにpartner_face_descriptionを書き込んでおく
    prof_path = os.path.join(DIR, f'../tmp/user_sessions/{session_id}/user_profile.json')
    import json
    if os.path.exists(prof_path):
        data = json.load(open(prof_path, encoding='utf-8'))
        data['partner_face_description'] = '目が大きくて優しい女性風'
        json.dump(data, open(prof_path,'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    payload = {'target': 'partner'}
    r = requests.post(f"{BASE}/sessions/{session_id}/generate-image", json=payload)
    print('パートナー画像生成:', r.status_code, r.json())
    return r.json()

# 4. 子ども画像合成API
def generate_child_image(session_id):
    r = requests.post(f"{BASE}/sessions/{session_id}/generate-child-image")
    print('子ども画像合成:', r.status_code, r.json())
    return r.json()

if __name__ == '__main__':
    sid = create_session()
    upload_user_image(sid)
    generate_partner_image(sid)
    generate_child_image(sid)
