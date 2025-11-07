# Supabase Auth + Google OAuth アーキテクチャ図

**作成日**: 2025-10-28
**目的**: 認証機能の詳細フローを視覚化

---

## 📋 目次

1. [認証フロー全体像](#1-認証フロー全体像)
2. [Googleログインシーケンス](#2-googleログインシーケンス)
3. [JWT検証フロー](#3-jwt検証フロー)
4. [Row Level Security（RLS）](#4-row-level-securityrls)
5. [フロントエンド画面遷移](#5-フロントエンド画面遷移)
6. [データモデル](#6-データモデル)
7. [セキュリティアーキテクチャ](#7-セキュリティアーキテクチャ)

---

## 1. 認証フロー全体像

```mermaid
graph TB
    subgraph "ユーザー"
        User[ユーザー]
    end

    subgraph "フロントエンド（Next.js）"
        LoginPage[ログイン画面]
        Dashboard[ダッシュボード]
        ChatPage[チャット画面]
    end

    subgraph "Supabase"
        Auth[Supabase Auth<br/>認証サービス]
        DB[(PostgreSQL<br/>+ RLS)]
        Storage[(Storage)]
    end

    subgraph "外部サービス"
        Google[Google OAuth]
    end

    subgraph "バックエンド（Flask）"
        API[API<br/>JWT検証]
    end

    User -->|1. アクセス| LoginPage
    LoginPage -->|2. Googleログイン| Auth
    Auth -->|3. OAuth認証| Google
    Google -->|4. 認証成功| Auth
    Auth -->|5. JWT発行| Dashboard

    Dashboard -->|6. APIリクエスト<br/>+ JWT| API
    API -->|7. JWT検証| Auth
    Auth -->|8. ユーザー情報| API
    API -->|9. データ取得| DB
    DB -->|10. RLS適用<br/>ユーザーデータのみ| API
    API -->|11. レスポンス| Dashboard

    ChatPage -->|同様のフロー| API

    style Auth fill:#3ecf8e
    style DB fill:#3ecf8e
    style Google fill:#4285f4
    style API fill:#ff6b6b
```

---

## 2. Googleログインシーケンス

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant Browser as ブラウザ<br/>Next.js
    participant SupaAuth as Supabase Auth
    participant Google as Google OAuth
    participant DB as PostgreSQL

    Note over User,DB: 初回ログイン

    User->>Browser: 「Googleでログイン」クリック
    Browser->>SupaAuth: signInWithOAuth({provider: 'google'})
    SupaAuth->>Google: OAuth認証リクエスト<br/>client_id + redirect_uri

    Note over Google: Googleログイン画面表示

    Google->>User: ログイン画面表示
    User->>Google: Googleアカウントで認証
    Google->>Google: 認証情報確認
    Google->>SupaAuth: 認証成功<br/>authorization_code

    SupaAuth->>Google: access_token リクエスト<br/>authorization_code + client_secret
    Google-->>SupaAuth: access_token + user_info

    SupaAuth->>DB: ユーザー情報を auth.users に保存
    DB-->>SupaAuth: ユーザー作成完了

    SupaAuth->>SupaAuth: JWT生成<br/>payload: {sub: user_id, email, ...}

    SupaAuth->>Browser: リダイレクト<br/>/dashboard?access_token=xxx

    Browser->>Browser: JWT を localStorage に保存

    Browser->>User: ダッシュボード表示

    Note over User,DB: 2回目以降のログイン

    User->>Browser: 「Googleでログイン」クリック
    Browser->>SupaAuth: signInWithOAuth({provider: 'google'})
    SupaAuth->>Google: OAuth認証リクエスト
    Google->>User: 既に認証済み（即座に承認）
    Google->>SupaAuth: authorization_code
    SupaAuth->>DB: 既存ユーザー確認
    DB-->>SupaAuth: ユーザー情報
    SupaAuth->>SupaAuth: JWT生成
    SupaAuth->>Browser: リダイレクト + JWT
    Browser->>User: ダッシュボード表示
```

---

## 3. JWT検証フロー

```mermaid
sequenceDiagram
    participant Frontend as Frontend
    participant Backend as Backend API
    participant Auth as Supabase Auth
    participant DB as PostgreSQL

    Note over Frontend,DB: 認証付きAPIリクエスト

    Frontend->>Frontend: localStorageからJWT取得

    Frontend->>Backend: POST /api/sessions<br/>Header: Authorization: Bearer <JWT>

    Backend->>Backend: JWT抽出<br/>Authorization Header から

    alt JWT検証成功
        Backend->>Backend: JWT検証<br/>署名・有効期限確認
        Backend->>Backend: ペイロード取得<br/>{sub: user_id, email, ...}
        Backend->>Backend: request.user_id = user_id

        Backend->>DB: セッション作成<br/>user_id と紐付け
        DB-->>Backend: 作成完了

        Backend-->>Frontend: 200 OK<br/>{session_id: "xxx"}

    else JWT検証失敗
        Backend->>Backend: JWT検証失敗<br/>（期限切れ or 無効）
        Backend-->>Frontend: 401 Unauthorized<br/>{error: "Invalid token"}

        Frontend->>Auth: リフレッシュトークンで再認証
        Auth-->>Frontend: 新しいJWT発行
        Frontend->>Backend: リトライ（新しいJWT）
    end
```

---

## 4. Row Level Security（RLS）

### 4.1 RLS適用の仕組み

```mermaid
graph TB
    subgraph "バックエンド"
        API[Flask API]
    end

    subgraph "PostgreSQL + RLS"
        Query[SQL Query<br/>SELECT * FROM sessions]
        RLSCheck{RLSポリシー<br/>チェック}
        FilteredData[フィルタされたデータ<br/>user_id = auth.uid()]
    end

    subgraph "Supabase Auth"
        AuthContext[認証コンテキスト<br/>auth.uid() = user_123]
    end

    API -->|1. JWTと共にクエリ| Query
    Query -->|2. RLS適用| RLSCheck
    RLSCheck -->|3. auth.uid()取得| AuthContext
    AuthContext -->|4. user_id = user_123| RLSCheck
    RLSCheck -->|5. WHERE user_id = 'user_123'<br/>自動追加| FilteredData
    FilteredData -->|6. ユーザーのデータのみ| API

    style RLSCheck fill:#f39c12
    style AuthContext fill:#3ecf8e
```

### 4.2 RLSポリシー例

```mermaid
graph LR
    subgraph "User A（user_id: aaa）"
        UserA[User A]
        SessionA1[Session A1<br/>user_id: aaa]
        SessionA2[Session A2<br/>user_id: aaa]
    end

    subgraph "User B（user_id: bbb）"
        UserB[User B]
        SessionB1[Session B1<br/>user_id: bbb]
    end

    subgraph "PostgreSQL + RLS"
        DB[(sessions table<br/>全データ)]
        RLS[RLS Policy:<br/>WHERE user_id = auth.uid]
    end

    UserA -->|リクエスト| RLS
    UserB -->|リクエスト| RLS

    RLS -->|フィルタ| DB
    DB -.->|User Aは見える| SessionA1
    DB -.->|User Aは見える| SessionA2
    DB -.->|User Aは見えない| SessionB1

    DB -.->|User Bは見える| SessionB1
    DB -.->|User Bは見えない| SessionA1
    DB -.->|User Bは見えない| SessionA2

    style SessionA1 fill:#e6ffe6
    style SessionA2 fill:#e6ffe6
    style SessionB1 fill:#ffe6e6
    style RLS fill:#f39c12
```

---

## 5. フロントエンド画面遷移

```mermaid
graph TB
    Start([アプリ起動])

    CheckAuth{ログイン済み？}
    LoginPage[ログイン画面<br/>/login]
    GoogleAuth[Google OAuth<br/>認証フロー]
    Dashboard[ダッシュボード<br/>/dashboard]
    ChatPage[チャット画面<br/>/chat]
    ProfilePage[プロフィール<br/>/profile]
    Logout[ログアウト]

    Start --> CheckAuth

    CheckAuth -->|NO| LoginPage
    CheckAuth -->|YES| Dashboard

    LoginPage -->|Googleログイン| GoogleAuth
    GoogleAuth -->|認証成功| Dashboard

    Dashboard -->|新しいチャット| ChatPage
    Dashboard -->|プロフィール編集| ProfilePage
    Dashboard -->|ログアウト| Logout

    ChatPage -->|戻る| Dashboard
    ProfilePage -->|戻る| Dashboard

    Logout --> LoginPage

    style LoginPage fill:#ffeaa7
    style Dashboard fill:#81ecec
    style ChatPage fill:#74b9ff
    style GoogleAuth fill:#4285f4
```

---

## 6. データモデル

### 6.1 認証関連テーブル

```mermaid
erDiagram
    auth_users ||--o{ sessions : "has many"
    sessions ||--o{ user_profiles : "has one"
    sessions ||--o{ conversation_history : "has many"
    sessions ||--o{ family_conversations : "has many"
    sessions ||--o{ session_images : "has many"

    auth_users {
        uuid id PK
        string email
        jsonb raw_user_meta_data
        timestamp created_at
        timestamp last_sign_in_at
    }

    sessions {
        uuid id PK
        string session_id UK
        uuid user_id FK
        string status
        timestamp created_at
        timestamp updated_at
    }

    user_profiles {
        uuid id PK
        string session_id FK
        string name
        int age
        string partner_name
        jsonb hobbies
        timestamp created_at
    }

    conversation_history {
        uuid id PK
        string session_id FK
        string speaker
        text message
        timestamp timestamp
    }

    family_conversations {
        uuid id PK
        string session_id FK
        string speaker
        text message
        timestamp timestamp
    }

    session_images {
        uuid id PK
        string session_id FK
        string image_type
        string storage_path
        string public_url
        timestamp created_at
    }
```

### 6.2 auth.users テーブル（Supabase管理）

```mermaid
graph TB
    subgraph "Supabase Auth Schema"
        AuthUsers[(auth.users<br/>Supabase管理)]

        AuthUsers -.->|構造| Structure["id: uuid<br/>email: string<br/>encrypted_password: string<br/>raw_user_meta_data: jsonb<br/>  ├─ full_name<br/>  ├─ avatar_url<br/>  └─ provider_id<br/>provider: string (google)<br/>created_at: timestamp<br/>last_sign_in_at: timestamp"]
    end

    subgraph "Public Schema"
        Sessions[(public.sessions<br/>アプリ管理)]
    end

    AuthUsers -->|user_id| Sessions

    style AuthUsers fill:#3ecf8e
    style Sessions fill:#74b9ff
```

---

## 7. セキュリティアーキテクチャ

```mermaid
graph TB
    subgraph "セキュリティ層"
        subgraph "Layer 1: ネットワーク"
            HTTPS[HTTPS<br/>TLS 1.3]
            CORS[CORS<br/>Origin制限]
        end

        subgraph "Layer 2: 認証"
            OAuth[Google OAuth<br/>信頼された認証]
            JWT[JWT<br/>署名付きトークン]
        end

        subgraph "Layer 3: 認可"
            RLS[Row Level Security<br/>データベースレベル]
            APIAuth[API認証<br/>@require_auth]
        end

        subgraph "Layer 4: データ"
            Encryption[データ暗号化<br/>at rest + in transit]
            Backup[自動バックアップ<br/>Point-in-Time Recovery]
        end
    end

    User[ユーザー] --> HTTPS
    HTTPS --> CORS
    CORS --> OAuth
    OAuth --> JWT
    JWT --> RLS
    RLS --> APIAuth
    APIAuth --> Encryption
    Encryption --> Backup

    style HTTPS fill:#27ae60
    style OAuth fill:#3498db
    style RLS fill:#f39c12
    style Encryption fill:#9b59b6
```

---

## 8. 実装の全体像

```mermaid
graph TB
    subgraph "Phase 1: 設定（1-2時間）"
        P1_1[Google OAuth設定]
        P1_2[Supabase Auth有効化]
        P1_3[環境変数設定]

        P1_1 --> P1_2
        P1_2 --> P1_3
    end

    subgraph "Phase 2: フロントエンド（4-6時間）"
        P2_1[Supabaseクライアント]
        P2_2[useAuth フック]
        P2_3[ログイン画面]
        P2_4[ダッシュボード]
        P2_5[ヘッダー]

        P2_1 --> P2_2
        P2_2 --> P2_3
        P2_3 --> P2_4
        P2_4 --> P2_5
    end

    subgraph "Phase 3: バックエンド（3-4時間）"
        P3_1[JWT検証ミドルウェア]
        P3_2[@require_auth追加]
        P3_3[user_id紐付け]
        P3_4[権限チェック]

        P3_1 --> P3_2
        P3_2 --> P3_3
        P3_3 --> P3_4
    end

    subgraph "Phase 4: RLS設定（2-3時間）"
        P4_1[スキーマ更新]
        P4_2[RLSポリシー作成]
        P4_3[データ移行]

        P4_1 --> P4_2
        P4_2 --> P4_3
    end

    subgraph "Phase 5: テスト（2-3時間）"
        P5_1[ログインテスト]
        P5_2[RLS動作確認]
        P5_3[統合テスト]

        P5_1 --> P5_2
        P5_2 --> P5_3
    end

    P1_3 --> P2_1
    P2_5 --> P3_1
    P3_4 --> P4_1
    P4_3 --> P5_1

    style P1_3 fill:#3498db
    style P2_5 fill:#3498db
    style P3_4 fill:#3498db
    style P4_3 fill:#f39c12
    style P5_3 fill:#27ae60
```

---

## 9. Before/After 比較

```mermaid
graph LR
    subgraph "Before（認証なし）"
        B1[ユーザー管理<br/>なし]
        B2[セッション管理<br/>session_idのみ]
        B3[データ分離<br/>なし]
        B4[セキュリティ<br/>低い]
    end

    subgraph "After（Supabase Auth）"
        A1[ユーザー管理<br/>Google OAuth]
        A2[セッション管理<br/>user_id + session_id]
        A3[データ分離<br/>RLS自動適用]
        A4[セキュリティ<br/>高い JWT + RLS]
    end

    B1 -.->|改善| A1
    B2 -.->|改善| A2
    B3 -.->|改善| A3
    B4 -.->|改善| A4

    style B1 fill:#ffe6e6
    style B2 fill:#ffe6e6
    style B3 fill:#ffe6e6
    style B4 fill:#ffe6e6

    style A1 fill:#e6ffe6
    style A2 fill:#e6ffe6
    style A3 fill:#e6ffe6
    style A4 fill:#e6ffe6
```

---

## 10. ログイン画面デザイン

```mermaid
graph TB
    subgraph "ログイン画面（/login）"
        Logo[Hera ロゴ<br/>大きく中央]
        Tagline[タグライン<br/>あなただけのAIパートナー]
        GoogleBtn[Googleでログイン<br/>ボタン]
        Terms[利用規約・プライバシーポリシー<br/>リンク]

        Logo --> Tagline
        Tagline --> GoogleBtn
        GoogleBtn --> Terms
    end

    GoogleBtn -.->|クリック| GoogleOAuth[Google OAuth画面]
    GoogleOAuth -.->|認証成功| Dashboard[ダッシュボード]

    style Logo fill:#e6f3ff
    style GoogleBtn fill:#4285f4
    style Dashboard fill:#e6ffe6
```

---

## まとめ

### ✅ 実装するもの

1. **Google OAuth設定**: Google Cloud Console + Supabase
2. **フロントエンド**: ログイン画面、ダッシュボード、認証フック
3. **バックエンド**: JWT検証ミドルウェア、user_id紐付け
4. **データベース**: RLSポリシー、user_idカラム追加
5. **テスト**: ログイン、RLS、統合テスト

### 📊 セキュリティ対策

1. **HTTPS**: 通信暗号化
2. **Google OAuth**: 信頼された認証
3. **JWT**: 署名付きトークン
4. **RLS**: データベースレベルのアクセス制御
5. **CORS**: Origin制限

### 🚀 所要時間

- **Phase 1（設定）**: 1-2時間
- **Phase 2（フロントエンド）**: 4-6時間
- **Phase 3（バックエンド）**: 3-4時間
- **Phase 4（RLS）**: 2-3時間
- **Phase 5（テスト）**: 2-3時間

**合計**: 12-18時間

### 💰 コスト

- **Supabase Auth**: $0（Freeプランで50,000 MAUまで無料）
- **Google OAuth**: $0（無料）

**追加コストなしで、強固な認証システムが構築できます！**
