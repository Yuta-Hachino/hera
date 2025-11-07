# Supabase統合アーキテクチャ図

本ドキュメントでは、Supabase統合後のシステムアーキテクチャを詳細に図示します。

---

## 1. Supabaseシステム全体構成

```mermaid
graph TB
    subgraph "ユーザー環境"
        User[ユーザー<br/>ブラウザ]
    end

    subgraph "Vercel"
        Frontend[Next.js Frontend<br/>:3000]
    end

    subgraph "Cloud Run / Vercel Serverless"
        Backend[Flask Backend<br/>:8080]
    end

    subgraph "Supabase Platform"
        subgraph "Database"
            PostgreSQL[(PostgreSQL<br/>セッション・会話データ)]
            Sessions[sessions]
            UserProfiles[user_profiles]
            Conversations[conversation_history]
            FamilyConv[family_conversations]
            TripInfo[family_trip_info]
            Plans[family_plans]
            Images[session_images]
        end

        subgraph "Storage"
            Storage[(Supabase Storage<br/>画像ファイル)]
            Bucket[session-images bucket]
        end

        subgraph "Features"
            Realtime[Realtime<br/>リアルタイム通知]
            Auth[Auth<br/>認証 - 将来用]
            API[REST API<br/>PostgREST]
        end
    end

    User -->|HTTP| Frontend
    Frontend -->|API Call| Backend
    Frontend -.->|Direct Access| PostgreSQL
    Frontend -.->|Direct Access| Storage
    Backend -->|REST API| PostgreSQL
    Backend -->|Storage API| Storage
    PostgreSQL -->|変更通知| Realtime
    Realtime -.->|WebSocket| Frontend
    PostgreSQL --> Sessions
    PostgreSQL --> UserProfiles
    PostgreSQL --> Conversations
    PostgreSQL --> FamilyConv
    PostgreSQL --> TripInfo
    PostgreSQL --> Plans
    PostgreSQL --> Images
    Storage --> Bucket

    style PostgreSQL fill:#3ecf8e
    style Storage fill:#3ecf8e
    style Realtime fill:#3ecf8e
    style Auth fill:#a8dadc
    style API fill:#3ecf8e
    style Backend fill:#4ecdc4
    style Frontend fill:#95e1d3
```

---

## 2. データベーススキーマ関係図

```mermaid
erDiagram
    sessions ||--o{ user_profiles : has
    sessions ||--o{ conversation_history : has
    sessions ||--o{ family_conversations : has
    sessions ||--o{ family_trip_info : has
    sessions ||--o{ family_plans : has
    sessions ||--o{ session_images : has

    sessions {
        uuid id PK
        text session_id UK
        timestamp created_at
        timestamp updated_at
        text status
    }

    user_profiles {
        uuid id PK
        text session_id FK
        text name
        int age
        text gender
        text occupation
        text partner_name
        int partner_age
        text partner_occupation
        text partner_face_description
        int relationship_years
        text relationship_status
        jsonb hobbies
        jsonb values
        jsonb lifestyle
        timestamp created_at
        timestamp updated_at
    }

    conversation_history {
        uuid id PK
        text session_id FK
        text speaker
        text message
        timestamp timestamp
        jsonb extracted_fields
    }

    family_conversations {
        uuid id PK
        text session_id FK
        text speaker
        text message
        timestamp timestamp
    }

    family_trip_info {
        uuid id PK
        text session_id FK
        text destination
        int duration_days
        int budget
        jsonb activities
        jsonb preferences
        timestamp created_at
        timestamp updated_at
    }

    family_plans {
        uuid id PK
        text session_id FK
        text story
        jsonb letters
        jsonb itinerary
        timestamp generated_at
    }

    session_images {
        uuid id PK
        text session_id FK
        text image_type
        text storage_path
        text public_url
        int file_size
        text mime_type
        timestamp created_at
    }
```

---

## 3. セッション作成フロー（Supabase版）

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Backend
    participant Supabase DB
    participant Supabase Storage

    User->>Frontend: アクセス
    Frontend->>Backend: POST /api/sessions

    Backend->>Backend: session_id = uuid.uuid4()

    rect rgb(200, 255, 220)
        Note over Backend,Supabase DB: Supabaseにセッション作成
        Backend->>Supabase DB: INSERT INTO sessions<br/>(session_id, status)
        Supabase DB-->>Backend: {id, session_id, created_at}
    end

    rect rgb(220, 240, 255)
        Note over Backend,Supabase DB: 初期プロファイル作成
        Backend->>Supabase DB: INSERT INTO user_profiles<br/>(session_id, ...)
        Supabase DB-->>Backend: OK
    end

    Backend-->>Frontend: {session_id, created_at, status}
    Frontend-->>User: セッション開始
```

---

## 4. メッセージ送信・保存フロー（Supabase版）

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Backend
    participant HeraAgent
    participant Gemini API
    participant Supabase DB
    participant Realtime

    User->>Frontend: メッセージ入力
    Frontend->>Backend: POST /api/sessions/{id}/messages<br/>{message: "..."}

    rect rgb(255, 245, 220)
        Note over Backend,Supabase DB: セッション確認
        Backend->>Supabase DB: SELECT * FROM sessions<br/>WHERE session_id = ?
        Supabase DB-->>Backend: session data
    end

    Backend->>HeraAgent: run(message, session_id)
    HeraAgent->>Gemini API: Generate Response
    Gemini API-->>HeraAgent: AI Response + 抽出データ
    HeraAgent-->>Backend: {message, user_profile, ...}

    rect rgb(220, 255, 220)
        Note over Backend,Supabase DB: プロファイル更新
        Backend->>Supabase DB: UPDATE user_profiles<br/>SET name=?, age=?<br/>WHERE session_id=?
        Supabase DB-->>Backend: OK
        Supabase DB->>Realtime: 変更通知
    end

    rect rgb(220, 240, 255)
        Note over Backend,Supabase DB: 会話履歴追加
        Backend->>Supabase DB: INSERT INTO conversation_history<br/>(session_id, speaker, message)
        Supabase DB-->>Backend: OK
        Supabase DB->>Realtime: 変更通知
    end

    Realtime-->>Frontend: WebSocket: 新しいメッセージ
    Backend-->>Frontend: {reply, user_profile, ...}
    Frontend-->>User: AI応答 + リアルタイム更新
```

---

## 5. 画像アップロード・保存フロー（Supabase版）

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Backend
    participant Supabase DB
    participant Supabase Storage

    User->>Frontend: 画像選択
    Frontend->>Backend: POST /api/sessions/{id}/photos/user<br/>FormData: file

    Backend->>Backend: validate file
    Backend->>Backend: file_data = file.read()

    rect rgb(220, 255, 240)
        Note over Backend,Supabase Storage: Supabase Storageにアップロード
        Backend->>Supabase Storage: upload(bucket, path, file_data)
        Supabase Storage-->>Backend: OK
        Backend->>Supabase Storage: get_public_url(path)
        Supabase Storage-->>Backend: public_url
    end

    rect rgb(220, 240, 255)
        Note over Backend,Supabase DB: メタデータ保存
        Backend->>Supabase DB: INSERT INTO session_images<br/>(session_id, image_type, storage_path, public_url)
        Supabase DB-->>Backend: OK
    end

    Backend-->>Frontend: {status: success, image_url}
    Frontend-->>User: アップロード完了
```

---

## 6. 画像取得フロー（Supabase版）

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Backend
    participant Supabase DB
    participant Supabase Storage

    User->>Frontend: 画像表示リクエスト

    alt フロントエンドから直接取得（推奨）
        Frontend->>Supabase DB: SELECT public_url FROM session_images<br/>WHERE session_id=? AND image_type=?
        Supabase DB-->>Frontend: {public_url}
        Frontend->>Frontend: <img src={public_url} />
        Frontend-->>User: 画像表示
    else バックエンド経由
        Frontend->>Backend: GET /api/sessions/{id}/photos/user.png
        Backend->>Supabase DB: SELECT storage_path FROM session_images
        Supabase DB-->>Backend: {storage_path}
        Backend->>Supabase Storage: download(storage_path)
        Supabase Storage-->>Backend: file_data
        Backend-->>Frontend: Response(file_data)
        Frontend-->>User: 画像表示
    end
```

---

## 7. リアルタイム更新フロー

```mermaid
sequenceDiagram
    participant Frontend1 as Frontend (ユーザー1)
    participant Frontend2 as Frontend (管理者)
    participant Supabase DB
    participant Realtime

    rect rgb(240, 240, 240)
        Note over Frontend1,Realtime: WebSocket接続確立
        Frontend1->>Realtime: subscribe('session:abc')
        Frontend2->>Realtime: subscribe('session:abc')
        Realtime-->>Frontend1: connected
        Realtime-->>Frontend2: connected
    end

    Frontend1->>Frontend1: ユーザーがメッセージ送信
    Frontend1->>Supabase DB: INSERT INTO conversation_history

    rect rgb(220, 255, 220)
        Note over Supabase DB,Realtime: 変更検知
        Supabase DB->>Realtime: postgres_changes event<br/>{table: conversation_history}
    end

    rect rgb(255, 240, 220)
        Note over Realtime,Frontend2: リアルタイム通知
        Realtime-->>Frontend1: 新しいメッセージ
        Realtime-->>Frontend2: 新しいメッセージ
    end

    Frontend1->>Frontend1: UI更新
    Frontend2->>Frontend2: UI更新（管理画面）
```

---

## 8. データ移行フロー（Redis → Supabase）

```mermaid
flowchart TB
    Start[移行開始] --> ReadRedis[Redis全キー取得]

    ReadRedis --> Loop{全セッション処理}

    Loop -->|次のセッション| ExtractSession[セッションデータ抽出]

    ExtractSession --> ExtractProfile[user_profile取得]
    ExtractSession --> ExtractHistory[conversation_history取得]
    ExtractSession --> ExtractFamily[family_conversation取得]
    ExtractSession --> ExtractTrip[family_trip_info取得]
    ExtractSession --> ExtractPlan[family_plan取得]

    ExtractProfile --> CreateSession[Supabase: sessions作成]
    CreateSession --> InsertProfile[Supabase: user_profiles挿入]
    ExtractHistory --> InsertHistory[Supabase: conversation_history挿入]
    ExtractFamily --> InsertFamily[Supabase: family_conversations挿入]
    ExtractTrip --> InsertTrip[Supabase: family_trip_info挿入]
    ExtractPlan --> InsertPlan[Supabase: family_plans挿入]

    InsertProfile --> CheckImages{画像あり?}
    InsertHistory --> CheckImages
    InsertFamily --> CheckImages
    InsertTrip --> CheckImages
    InsertPlan --> CheckImages

    CheckImages -->|Yes| UploadImages[Supabase Storageにアップロード]
    CheckImages -->|No| NextSession

    UploadImages --> InsertImageMeta[session_images挿入]
    InsertImageMeta --> NextSession[次のセッションへ]

    NextSession --> Loop

    Loop -->|完了| Verify[データ検証]
    Verify --> Cleanup[Redisクリーンアップ]
    Cleanup --> End[移行完了]

    style Start fill:#51cf66
    style End fill:#51cf66
    style CreateSession fill:#3ecf8e
    style InsertProfile fill:#3ecf8e
    style InsertHistory fill:#3ecf8e
    style UploadImages fill:#74b9ff
```

---

## 9. Row Level Security (RLS) ポリシー

```mermaid
graph TB
    subgraph "認証なし（開発用）"
        Public[Public Access<br/>全テーブル読み取り可]
    end

    subgraph "認証あり（本番用）"
        Auth[認証済みユーザー]

        Auth --> Sessions[sessions<br/>自分のセッションのみ]
        Auth --> Profiles[user_profiles<br/>自分のセッションのみ]
        Auth --> Conversations[conversation_history<br/>自分のセッションのみ]
        Auth --> Images[session_images<br/>自分のセッションのみ]

        Sessions --> Read1[SELECT: 可]
        Sessions --> Write1[INSERT/UPDATE: 可]
        Sessions --> Delete1[DELETE: 不可]

        Profiles --> Read2[SELECT: 可]
        Profiles --> Write2[INSERT/UPDATE: 可]

        Conversations --> Read3[SELECT: 可]
        Conversations --> Write3[INSERT: 可]

        Images --> Read4[SELECT: 可]
        Images --> Write4[INSERT: 可]
    end

    style Public fill:#ff6b6b
    style Auth fill:#51cf66
    style Sessions fill:#3ecf8e
    style Profiles fill:#3ecf8e
    style Conversations fill:#3ecf8e
    style Images fill:#3ecf8e
```

### RLSポリシー設定例

```sql
-- sessions テーブル: 認証済みユーザーは自分のセッションのみアクセス可
CREATE POLICY "Users can view own sessions"
ON sessions FOR SELECT
USING (auth.uid()::text = session_id);

CREATE POLICY "Users can insert own sessions"
ON sessions FOR INSERT
WITH CHECK (auth.uid()::text = session_id);

-- user_profiles テーブル
CREATE POLICY "Users can view own profiles"
ON user_profiles FOR SELECT
USING (session_id IN (
    SELECT session_id FROM sessions
    WHERE auth.uid()::text = session_id
));

-- conversation_history テーブル
CREATE POLICY "Users can view own conversations"
ON conversation_history FOR SELECT
USING (session_id IN (
    SELECT session_id FROM sessions
    WHERE auth.uid()::text = session_id
));

-- 開発用: 全アクセス許可（本番では削除）
CREATE POLICY "Allow all for development"
ON sessions FOR ALL
USING (true);
```

---

## 10. Supabase Storage バケット構造

```mermaid
graph TB
    subgraph "Supabase Storage"
        Bucket[session-images<br/>Public Bucket]

        Bucket --> Session1[{session_id_1}/]
        Bucket --> Session2[{session_id_2}/]
        Bucket --> Session3[...]

        Session1 --> User1[user.png]
        Session1 --> Partner1[partner.png]
        Session1 --> Child1[child_1.png]

        Session2 --> User2[user.png]
        Session2 --> Partner2[partner.png]
    end

    subgraph "アクセス制御"
        PublicRead[Public Read<br/>誰でも画像取得可]
        AuthWrite[Authenticated Write<br/>認証済みのみアップロード可]
    end

    User1 -.-> PublicRead
    Partner1 -.-> PublicRead
    User2 -.-> AuthWrite
    Partner2 -.-> AuthWrite

    style Bucket fill:#3ecf8e
    style PublicRead fill:#74b9ff
    style AuthWrite fill:#ffd43b
```

### Storage ポリシー設定

```sql
-- 誰でも画像取得可能
CREATE POLICY "Public can view images"
ON storage.objects FOR SELECT
USING (bucket_id = 'session-images');

-- 認証済みユーザーのみアップロード可能
CREATE POLICY "Authenticated users can upload"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'session-images' AND
    auth.role() = 'authenticated'
);
```

---

## 11. 環境別デプロイ構成

```mermaid
graph TB
    subgraph "ローカル開発"
        LocalFE[Frontend<br/>localhost:3000]
        LocalBE[Backend<br/>localhost:8080]
        LocalSupabase[Supabase CLI<br/>localhost:54321]

        LocalFE --> LocalBE
        LocalBE --> LocalSupabase
        LocalFE -.-> LocalSupabase
    end

    subgraph "ステージング"
        StageFE[Vercel Preview]
        StageBE[Cloud Run Dev]
        StageSupabase[Supabase Project<br/>staging]

        StageFE --> StageBE
        StageBE --> StageSupabase
        StageFE -.-> StageSupabase
    end

    subgraph "本番"
        ProdFE[Vercel Production]
        ProdBE[Cloud Run Production]
        ProdSupabase[Supabase Project<br/>production]

        ProdFE --> ProdBE
        ProdBE --> ProdSupabase
        ProdFE -.-> ProdSupabase
    end

    style LocalSupabase fill:#a8dadc
    style StageSupabase fill:#3ecf8e
    style ProdSupabase fill:#3ecf8e
```

---

## 12. コスト構造比較

```mermaid
graph LR
    subgraph "現在（Redis + S3）"
        R1[ElastiCache<br/>$15/月]
        R2[S3<br/>$5/月]
        RTotal[合計: $20/月]

        R1 --> RTotal
        R2 --> RTotal
    end

    subgraph "Supabase"
        S1[Supabase Pro<br/>$25/月]
        S2[全機能含む<br/>DB + Storage + Realtime]
        STotal[合計: $25/月]

        S1 --> S2
        S2 --> STotal
    end

    RTotal -.->|+$5/月| STotal

    style RTotal fill:#ff6b6b
    style STotal fill:#51cf66
```

---

## 13. パフォーマンス比較

```mermaid
graph TB
    subgraph "Redis構成"
        RedisReq[リクエスト]
        RedisReq --> RedisBackend[Backend]
        RedisBackend --> RedisCache[(Redis Cache)]
        RedisBackend --> RedisS3[(S3)]
        RedisS3 --> RedisResp[レスポンス]
        RedisCache --> RedisResp

        RedisLatency[平均レイテンシ:<br/>50-100ms]
    end

    subgraph "Supabase構成"
        SupaReq[リクエスト]

        SupaReq --> SupaBackend[Backend]
        SupaBackend --> SupaDB[(Supabase DB)]

        SupaReq -.->|直接アクセス| SupaDB
        SupaReq -.->|直接アクセス| SupaStorage[(Supabase Storage)]

        SupaDB --> SupaResp[レスポンス]
        SupaStorage --> SupaResp

        SupaLatency[平均レイテンシ:<br/>30-80ms<br/>直接アクセス: 20-50ms]
    end

    style RedisLatency fill:#ffd43b
    style SupaLatency fill:#51cf66
```

---

## 補足説明

### Supabase接続情報

```bash
# .env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key  # バックエンド用
SUPABASE_BUCKET=session-images

# フロントエンド用
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### API エンドポイント

```
REST API: https://your-project.supabase.co/rest/v1/
Realtime: wss://your-project.supabase.co/realtime/v1/
Storage: https://your-project.supabase.co/storage/v1/
Auth: https://your-project.supabase.co/auth/v1/
```

---

このドキュメントは、Supabase統合後のシステムアーキテクチャを完全に表現しています。
