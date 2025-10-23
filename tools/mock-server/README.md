# Mock API Server

AI Family Simulator用のモックAPIサーバー

## セットアップ

```bash
cd tools/mock-server
npm install
```

## 起動方法

### 簡単起動（推奨）
```bash
./start-mock.sh
```

### 手動起動
```bash
npm run start:custom
```

## 利用可能なエンドポイント

### RESTful Resources
- `GET /api/v1/users` - ユーザー一覧
- `GET /api/v1/users/:id` - ユーザー詳細
- `POST /api/v1/users` - ユーザー作成
- `PUT /api/v1/users/:id` - ユーザー更新
- `DELETE /api/v1/users/:id` - ユーザー削除

同様に以下のリソースも利用可能:
- `/api/v1/sessions`
- `/api/v1/stories`
- `/api/v1/letters`
- `/api/v1/images`

### カスタムエンドポイント

#### シミュレーション実行
```bash
POST /api/v1/simulate
Content-Type: application/json

{
  "user_data": {
    "age": 28,
    "income": "medium",
    "lifestyle": "urban"
  }
}
```

#### ストーリー生成
```bash
POST /api/v1/stories/generate
Content-Type: application/json

{
  "session_id": "session_001",
  "scenario": "park"
}
```

#### 手紙生成
```bash
POST /api/v1/letters/generate
Content-Type: application/json

{
  "session_id": "session_001",
  "from_member": "daughter_5"
}
```

#### 画像生成
```bash
POST /api/v1/images/generate
Content-Type: application/json

{
  "session_id": "session_001",
  "prompt": "Happy family at the beach",
  "style": "realistic"
}
```

#### ヘルスチェック
```bash
GET /api/v1/health
```

## データの編集

`db.json` ファイルを編集することで、モックデータをカスタマイズできます。

サーバーは自動的にファイルの変更を検出してリロードします。

## ポート設定

デフォルトポート: `3001`

環境変数で変更可能:
```bash
PORT=4000 npm run start:custom
```

## 特徴

- CORS対応（すべてのオリジンから利用可能）
- 300msの遅延レスポンス（リアルなAPI動作をシミュレート）
- フルRESTful API対応
- カスタムエンドポイント対応
- ホットリロード対応
