# Hera プロジェクト デプロイガイド

このガイドでは、GCP Cloud Run + Supabase 構成でHeraプロジェクトをデプロイする手順を説明します。

## 目次

1. [前提条件](#前提条件)
2. [Phase 1: Supabaseセットアップ](#phase-1-supabaseセットアップ)
3. [Phase 2: Google Cloud Projectセットアップ](#phase-2-google-cloud-projectセットアップ)
4. [Phase 3: Google OAuth設定](#phase-3-google-oauth設定)
5. [Phase 4: ローカル開発環境セットアップ](#phase-4-ローカル開発環境セットアップ)
6. [Phase 5: Cloud Runデプロイ](#phase-5-cloud-runデプロイ)
7. [Phase 6: 動作確認](#phase-6-動作確認)

---

## 前提条件

- Node.js 18以上
- Python 3.10以上
- Google Cloud SDK (gcloud CLI)
- Gemini API Key

---

## Phase 1: Supabaseセットアップ

### 1.1 Supabaseプロジェクト作成

1. [Supabase](https://supabase.com) にアクセスし、サインアップ/ログイン
2. 「New Project」をクリック
3. プロジェクト情報を入力:
   - Name: `Hera Production`
   - Database Password: 強固なパスワードを生成（保存しておく）
   - Region: `Northeast Asia (Tokyo)`
4. 「Create new project」をクリック

### 1.2 API認証情報の取得

1. Supabaseダッシュボードで **Settings** > **API** に移動
2. 以下の情報をコピー:
   - `Project URL` (例: https://xxxxx.supabase.co)
   - `anon public` key
   - `service_role` key (⚠️ 秘密情報！)
3. **Settings** > **API** > **JWT Settings** で:
   - `JWT Secret` をコピー

### 1.3 データベーススキーマ作成

1. Supabaseダッシュボードで **SQL Editor** に移動
2. 以下のSQLを実行:

```sql
-- UUID拡張を有効化
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- セッションテーブル
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT UNIQUE NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'active'
);

CREATE INDEX idx_sessions_session_id ON sessions(session_id);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);

-- ユーザープロファイルテーブル
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    name TEXT,
    age INTEGER,
    partner_name TEXT,
    partner_age INTEGER,
    partner_face_description TEXT,
    hobbies JSONB DEFAULT '[]',
    children JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id)
);

-- 会話履歴テーブル
CREATE TABLE conversation_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    speaker TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_conversation_session_id ON conversation_history(session_id);
CREATE INDEX idx_conversation_order ON conversation_history(session_id, order_index);

-- 家族会話テーブル
CREATE TABLE family_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    speaker TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_family_conv_session_id ON family_conversations(session_id);
CREATE INDEX idx_family_conv_order ON family_conversations(session_id, order_index);

-- 家族旅行情報テーブル
CREATE TABLE family_trip_info (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    destination TEXT,
    activities JSONB DEFAULT '[]',
    trip_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id)
);

-- 家族計画テーブル
CREATE TABLE family_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    destination TEXT,
    activities JSONB DEFAULT '[]',
    story TEXT,
    letter TEXT,
    plan_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id)
);

-- セッション画像テーブル
CREATE TABLE session_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    image_type TEXT NOT NULL, -- 'user', 'partner', 'child_1', etc.
    image_url TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id, image_type)
);
```

### 1.4 Row Level Security (RLS) 設定

```sql
-- セッションテーブルのRLS
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own sessions"
ON sessions FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own sessions"
ON sessions FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sessions"
ON sessions FOR UPDATE
USING (auth.uid() = user_id);

-- ユーザープロファイルテーブルのRLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profiles"
ON user_profiles FOR SELECT
USING (
    auth.uid() = (SELECT user_id FROM sessions WHERE sessions.session_id = user_profiles.session_id)
);

CREATE POLICY "Users can insert own profiles"
ON user_profiles FOR INSERT
WITH CHECK (
    auth.uid() = (SELECT user_id FROM sessions WHERE sessions.session_id = user_profiles.session_id)
);

CREATE POLICY "Users can update own profiles"
ON user_profiles FOR UPDATE
USING (
    auth.uid() = (SELECT user_id FROM sessions WHERE sessions.session_id = user_profiles.session_id)
);

-- 他のテーブルも同様のRLSポリシーを設定
-- (conversation_history, family_conversations, family_trip_info, family_plans, session_images)
```

### 1.5 Supabase Storage バケット作成

1. Supabaseダッシュボードで **Storage** に移動
2. 「New bucket」をクリック
3. バケット情報を入力:
   - Name: `session-images`
   - Public: チェックを外す（プライベート）
4. 「Create bucket」をクリック

---

## Phase 2: Google Cloud Projectセットアップ

### 2.1 GCPプロジェクト作成

```bash
# gcloud CLIでログイン
gcloud auth login

# 新しいプロジェクトを作成
gcloud projects create hera-production --name="Hera Production"

# プロジェクトを選択
gcloud config set project hera-production

# 請求アカウントをリンク（請求アカウントIDを確認）
gcloud billing accounts list
gcloud billing projects link hera-production --billing-account=BILLING_ACCOUNT_ID
```

### 2.2 必要なAPIを有効化

```bash
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com
```

---

## Phase 3: Google OAuth設定

### 3.1 OAuth 2.0 クライアントID作成

1. [Google Cloud Console](https://console.cloud.google.com) にアクセス
2. プロジェクト `hera-production` を選択
3. **APIs & Services** > **Credentials** に移動
4. 「CREATE CREDENTIALS」> 「OAuth client ID」をクリック
5. Application type: `Web application`
6. Name: `Hera Frontend`
7. Authorized JavaScript origins:
   - `http://localhost:3000` (開発用)
   - `https://your-supabase-project.supabase.co` (本番用)
8. Authorized redirect URIs:
   - `https://your-supabase-project.supabase.co/auth/v1/callback`
9. 「CREATE」をクリック
10. **Client ID** と **Client Secret** をコピー

### 3.2 Supabase Auth設定

1. Supabaseダッシュボードで **Authentication** > **Providers** に移動
2. 「Google」を選択
3. 「Enabled」をオンにする
4. Google OAuth情報を入力:
   - Client ID: (3.1でコピーしたもの)
   - Client Secret: (3.1でコピーしたもの)
5. 「Save」をクリック

---

## Phase 4: ローカル開発環境セットアップ

### 4.1 依存関係のインストール

```bash
# バックエンド
cd backend
pip install -r requirements.txt
cd ..

# フロントエンド
cd frontend
npm install
cd ..
```

### 4.2 環境変数の設定

**backend/.env**
```bash
cp backend/.env.example backend/.env
```

`backend/.env` を編集:
```
GEMINI_API_KEY=your_gemini_api_key

SESSION_TYPE=supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_JWT_SECRET=your_jwt_secret

STORAGE_MODE=supabase

FLASK_DEBUG=True
PORT=8080
ALLOWED_ORIGINS=http://localhost:3000
```

**frontend/.env.local**
```bash
cp frontend/.env.example frontend/.env.local
```

`frontend/.env.local` を編集:
```
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
NEXT_PUBLIC_API_URL=http://localhost:8080
```

### 4.3 ローカルで起動

```bash
# ターミナル1: バックエンド
cd backend
python api/app.py

# ターミナル2: フロントエンド
cd frontend
npm run dev
```

ブラウザで http://localhost:3000 にアクセスして動作確認。

---

## Phase 5: Cloud Runデプロイ

### 5.1 環境変数のエクスポート

```bash
export GCP_PROJECT_ID=hera-production
export GCP_REGION=asia-northeast1
export SUPABASE_URL=https://xxxxx.supabase.co
export SUPABASE_ANON_KEY=your_anon_key
export SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
export SUPABASE_JWT_SECRET=your_jwt_secret
export GEMINI_API_KEY=your_gemini_api_key
```

### 5.2 デプロイ実行

```bash
# デプロイスクリプトに実行権限を付与
chmod +x deploy-cloud-run.sh

# 全サービスをデプロイ
./deploy-cloud-run.sh all

# または個別にデプロイ
./deploy-cloud-run.sh backend
./deploy-cloud-run.sh frontend
./deploy-cloud-run.sh adk
```

### 5.3 CORS設定の更新

バックエンドのデプロイ後、フロントエンドのURLを使って `ALLOWED_ORIGINS` を更新:

```bash
gcloud run services update hera-backend \
    --region=asia-northeast1 \
    --update-env-vars="ALLOWED_ORIGINS=https://hera-frontend-xxxx.run.app" \
    --project=hera-production
```

---

## Phase 6: 動作確認

### 6.1 動作確認チェックリスト

- [ ] フロントエンドURLにアクセスできる
- [ ] ログインページが表示される
- [ ] Googleアカウントでログインできる
- [ ] ダッシュボードが表示される
- [ ] 新しいセッションを作成できる
- [ ] ヘーラーとチャットできる
- [ ] セッションが完了できる
- [ ] 家族エージェントとチャットできる

### 6.2 ログ確認

```bash
# バックエンドのログ
gcloud run services logs read hera-backend --region=asia-northeast1 --project=hera-production

# フロントエンドのログ
gcloud run services logs read hera-frontend --region=asia-northeast1 --project=hera-production

# ADKのログ
gcloud run services logs read hera-adk --region=asia-northeast1 --project=hera-production
```

---

## トラブルシューティング

### 認証エラー

- Supabase JWTシークレットが正しく設定されているか確認
- Google OAuth認証のリダイレクトURIが正しいか確認

### データベース接続エラー

- Supabase URLとService Role Keyが正しいか確認
- RLSポリシーが正しく設定されているか確認

### Cloud Run デプロイエラー

- gcloud CLIが最新版か確認: `gcloud components update`
- 必要なAPIが有効化されているか確認
- 環境変数が正しく設定されているか確認

---

## コスト見積もり

### 月額コスト（想定: 100ユーザー/日）

- **Supabase Pro**: $25/月
- **Cloud Run**:
  - Frontend: $5/月
  - Backend: $5/月
  - ADK: $5/月
- **合計**: 約 $40/月

---

## 次のステップ

1. カスタムドメインの設定
2. Cloud Armor でセキュリティ強化
3. Cloud Monitoring でアラート設定
4. CI/CD パイプライン構築（GitHub Actions等）

---

## サポート

問題が発生した場合は、以下を確認してください:

1. 環境変数が正しく設定されているか
2. Supabaseのダッシュボードでエラーログを確認
3. Cloud Runのログを確認

詳細なドキュメント:
- [Supabase Docs](https://supabase.com/docs)
- [Cloud Run Docs](https://cloud.google.com/run/docs)
