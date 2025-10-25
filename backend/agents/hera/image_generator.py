"""
家族画像生成サービス
Gemini 2.5 Flash Imageを使用して家族の画像を生成する
"""
import base64
import os
import asyncio
from typing import List, Dict, Optional
from PIL import Image
import io
from google import genai


class FamilyImageGenerator:
    """家族画像生成クラス"""

    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY環境変数が設定されていません")
        self.client = genai.Client(api_key=self.gemini_api_key)
        self.current_session = None

    async def generate_partner_image(self, ideal_partner: dict) -> str:
        """奥さんの画像生成（ideal_partner.appearanceを使用）"""
        appearance = ideal_partner.get('appearance', '')
        temperament = ideal_partner.get('temperament', '')
        speaking_style = ideal_partner.get('speaking_style', '')

        prompt = f"""
        以下の特徴を持つ日本人女性の肖像画を生成してください：
        - 外見: {appearance}
        - 性格: {temperament}
        - 話し方: {speaking_style}

        温かく親しみやすい表情で、家族写真に適した自然な笑顔で描いてください。
        高品質で写実的なスタイルで。
        """

        print(f"[INFO] パートナー画像生成開始: {appearance[:50]}...")

        try:
            # Gemini 2.5 Flash Imageで画像生成
            partner_image_path = await self._generate_image_with_gemini_flash(prompt, "partner")
            print(f"[INFO] パートナー画像生成完了: {partner_image_path}")
            return partner_image_path
        except Exception as e:
            print(f"[ERROR] パートナー画像生成エラー: {e}")
            raise

    async def get_user_image_path(self, session_id: str) -> Optional[str]:
        """既存のユーザー画像パスを取得"""
        photos_dir = f"/Users/naoya.yasuda/Geniac-Prize/geechs-ai-hackathon-202510-team-a/backend/tmp/user_sessions/{session_id}/photos/"

        if not os.path.exists(photos_dir):
            print(f"[WARN] ユーザー画像ディレクトリが存在しません: {photos_dir}")
            return None

        # ユーザー画像ファイルを探す
        for ext in ['jpg', 'jpeg', 'png']:
            user_image_path = f"{photos_dir}user.{ext}"
            if os.path.exists(user_image_path):
                print(f"[INFO] ユーザー画像を発見: {user_image_path}")
                return user_image_path

        print(f"[WARN] ユーザー画像が見つかりません: {photos_dir}")
        return None

    async def generate_children_images(self, children_info: List[Dict],
                                     partner_image_path: str, user_image_path: str) -> List[Dict]:
        """子供の画像生成（両親の画像をインプットとして使用）"""
        children_images = []

        print(f"[INFO] 子供画像生成開始: {len(children_info)}名")

        for child in children_info:
            try:
                # 両親の画像を読み込み
                user_image = Image.open(user_image_path)
                partner_image = Image.open(partner_image_path)

                # プロンプト作成
                prompt = f"""
                以下の2枚の画像の人物を親とする{child['desired_gender']}の子の肖像画を生成してください：
                - 名前: {child['name']}
                - 性別: {child['desired_gender']}
                - 両親の特徴を自然に組み合わせた顔立ちで描いてください

                元気で可愛らしい表情で、家族写真に適した自然な笑顔で描いてください。
                高品質で写実的なスタイルで。
                """

                # Gemini 2.5 Flash Imageでマルチモーダル画像生成
                child_image_path = await self._generate_image_with_parents(
                    prompt,
                    user_image,
                    partner_image,
                    f"child_{child['name']}"
                )

                children_images.append({
                    'name': child['name'],
                    'gender': child['desired_gender'],
                    'image_path': child_image_path
                })

                print(f"[INFO] 子供画像生成完了: {child['name']} -> {child_image_path}")

            except Exception as e:
                print(f"[ERROR] 子供画像生成エラー ({child['name']}): {e}")
                # エラーでも続行
                continue

        return children_images

    async def _generate_image_with_parents(self, prompt: str, user_image: Image.Image,
                                         partner_image: Image.Image, filename: str) -> str:
        """両親の画像をインプットとして使用して子供の画像を生成"""
        try:
            print(f"[DEBUG] Gemini Flash Imageマルチモーダル生成開始: {filename}")

            # 画像をバイト配列に変換
            user_buffer = io.BytesIO()
            user_image.save(user_buffer, format='PNG')
            user_image_bytes = user_buffer.getvalue()

            partner_buffer = io.BytesIO()
            partner_image.save(partner_buffer, format='PNG')
            partner_image_bytes = partner_buffer.getvalue()

            # Gemini 2.5 Flash Imageでマルチモーダル画像生成
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image-preview",
                contents=[
                    prompt,
                    {"inline_data": {"mime_type": "image/png", "data": user_image_bytes}},
                    {"inline_data": {"mime_type": "image/png", "data": partner_image_bytes}}
                ]
            )

            print(f"[DEBUG] Gemini Flash Imageマルチモーダルレスポンス受信")

            # セッションディレクトリに保存
            session_dir = f"/Users/naoya.yasuda/Geniac-Prize/geechs-ai-hackathon-202510-team-a/backend/tmp/user_sessions/{self.current_session}/photos/"
            os.makedirs(session_dir, exist_ok=True)

            image_path = f"{session_dir}{filename}.jpg"

            # レスポンスから画像データを抽出
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    # 画像データを保存
                    image_data = part.inline_data.data
                    with open(image_path, "wb") as f:
                        f.write(image_data)

                    print(f"[INFO] マルチモーダル画像保存完了: {image_path} ({len(image_data)} bytes)")
                    return image_path
                elif part.text is not None:
                    print(f"[DEBUG] テキストレスポンス: {part.text}")

            raise Exception("画像データが見つかりませんでした")

        except Exception as e:
            print(f"[ERROR] Gemini Flash Imageマルチモーダル生成エラー: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def _generate_image_with_gemini_flash(self, prompt: str, filename: str) -> str:
        """Gemini 2.5 Flash Imageを使用して画像を生成"""
        try:
            print(f"[DEBUG] Gemini Flash Image生成開始: {filename}")

            # Gemini 2.5 Flash Imageで画像生成
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image-preview",
                contents=[prompt]
            )

            print(f"[DEBUG] Gemini Flash Imageレスポンス受信")

            # セッションディレクトリに保存
            session_dir = f"/Users/naoya.yasuda/Geniac-Prize/geechs-ai-hackathon-202510-team-a/backend/tmp/user_sessions/{self.current_session}/photos/"
            os.makedirs(session_dir, exist_ok=True)

            image_path = f"{session_dir}{filename}.jpg"

            # レスポンスから画像データを抽出
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    # 画像データを保存
                    image_data = part.inline_data.data
                    with open(image_path, "wb") as f:
                        f.write(image_data)

                    print(f"[INFO] 画像保存完了: {image_path} ({len(image_data)} bytes)")
                    return image_path
                elif part.text is not None:
                    print(f"[DEBUG] テキストレスポンス: {part.text}")

            raise Exception("画像データが見つかりませんでした")

        except Exception as e:
            print(f"[ERROR] Gemini Flash Image生成エラー: {e}")
            import traceback
            traceback.print_exc()
            raise
