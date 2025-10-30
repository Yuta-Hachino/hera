# システム構成図と処理フロー

本ドキュメントでは、Redis統合後のシステム構成と処理フローを詳細に説明します。

---

## 1. システム全体構成図

```mermaid
graph TB
    subgraph "ユーザー環境"
        User[ユーザー<br/>ブラウザ]
    end

    subgraph "Docker環境 (hera-network)"
        Frontend[Frontend<br/>Next.js:3000]
        Backend[Backend<br/>Flask:8080]
        ADK[Google ADK<br/>開発UI:8000]
        Redis[(Redis<br/>:6379)]

        subgraph "永続化ストレージ"
            RedisData[redis-data<br/>volume]
            SessionData[backend-sessions<br/>volume]
            Logs[backend-logs<br/>volume]
        end
    end

    subgraph "クラウド環境 (Production)"
        S3[(S3/GCS<br/>画像ストレージ)]
        CloudRedis[(Managed Redis<br/>ElastiCache/Memorystore)]
    end

    User -->|HTTP| Frontend
    Frontend -->|API Call| Backend
    Backend -->|セッション管理| Redis
    ADK -->|セッション共有| Redis
    Backend -->|画像保存| SessionData
    Backend -.->|Production| S3
    Backend -.->|Production| CloudRedis
    Redis -->|永続化| RedisData
    Backend -->|ログ| Logs
    ADK -->|ログ| Logs

    style Redis fill:#ff6b6b
    style Backend fill:#4ecdc4
    style Frontend fill:#95e1d3
    style ADK fill:#f9ca24
    style S3 fill:#a29bfe
    style CloudRedis fill:#fd79a8
```

---

## 2. データフロー概要

```mermaid
flowchart LR
    subgraph "セッションデータ"
        SD1[user_profile]
        SD2[conversation_history]
        SD3[family_conversation]
        SD4[family_trip_info]
    end

    subgraph "画像データ"
        ID1[user.png]
        ID2[partner.png]
        ID3[child_1.png]
    end

    Backend -->|save/load| Redis
    ADK -->|save/load| Redis
    Redis -->|保存| SD1
    Redis -->|保存| SD2
    Redis -->|保存| SD3
    Redis -->|保存| SD4

    Backend -->|save/load| Storage
    Storage -->|ローカル| LocalFS[ファイルシステム]
    Storage -.->|Production| Cloud[S3/GCS/Azure]
    LocalFS -->|保存| ID1
    LocalFS -->|保存| ID2
    LocalFS -->|保存| ID3

    style Redis fill:#ff6b6b
    style Storage fill:#a29bfe
    style LocalFS fill:#74b9ff
    style Cloud fill:#fd79a8
```

---

## 3. セッション作成フロー

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Backend
    participant Redis
    participant FileSystem

    User->>Frontend: アクセス
    Frontend->>Backend: POST /api/sessions

    Backend->>Backend: session_id = uuid.uuid4()

    rect rgb(200, 220, 255)
        Note over Backend,Redis: セッション初期化（Redis）
        Backend->>Redis: save(session_id, "user_profile", {})
        Backend->>Redis: save(session_id, "conversation_history", [])
        Backend->>Redis: save(session_id, "created_at", timestamp)
        Redis-->>Backend: OK
    end

    rect rgb(255, 220, 200)
        Note over Backend,FileSystem: 画像用ディレクトリ作成
        Backend->>FileSystem: mkdir photos/
        FileSystem-->>Backend: OK
    end

    Backend->>Backend: hera_agent.start_session()
    Backend-->>Frontend: {session_id, created_at, status}
    Frontend-->>User: セッション開始
```

---

## 4. メッセージ送信・AI応答フロー

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Backend
    participant HeraAgent
    participant Redis
    participant Gemini API

    User->>Frontend: メッセージ入力
    Frontend->>Backend: POST /api/sessions/{id}/messages<br/>{message: "..."}

    rect rgb(255, 240, 200)
        Note over Backend,Redis: セッション存在確認
        Backend->>Redis: exists(session_id)
        Redis-->>Backend: True
    end

    Backend->>HeraAgent: run(message, session_id)
    HeraAgent->>Gemini API: Generate Response
    Gemini API-->>HeraAgent: AI Response + 抽出データ

    HeraAgent-->>Backend: {message, user_profile, information_progress}

    rect rgb(200, 255, 200)
        Note over Backend,Redis: プロファイル保存
        Backend->>Backend: prune_empty_fields(profile)
        Backend->>Redis: save(session_id, "user_profile", profile)
        Redis-->>Backend: OK
    end

    rect rgb(200, 220, 255)
        Note over Backend,Redis: 会話履歴読み込み
        Backend->>Redis: load(session_id, "conversation_history")
        Redis-->>Backend: history[]
    end

    Backend->>Backend: build_information_progress()
    Backend->>Backend: compute_missing_fields()

    Backend-->>Frontend: {reply, user_profile, information_progress, missing_fields}
    Frontend-->>User: AI応答表示 + 進捗更新
```

---

## 5. 画像アップロードフロー

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Backend
    participant Redis
    participant StorageManager
    participant LocalFS as ローカルFS
    participant S3 as S3/GCS

    User->>Frontend: 画像選択・アップロード
    Frontend->>Backend: POST /api/sessions/{id}/photos/user<br/>FormData: file

    rect rgb(255, 240, 200)
        Note over Backend,Redis: セッション確認
        Backend->>Redis: exists(session_id)
        Redis-->>Backend: True
    end

    Backend->>Backend: validate file extension
    Backend->>Backend: file_data = file.read()

    alt ローカル開発環境 (STORAGE_MODE=redis)
        Backend->>StorageManager: save_file(session_id, "photos/user.png", data)
        StorageManager->>LocalFS: write to /tmp/user_sessions/{id}/photos/
        LocalFS-->>StorageManager: file path
        StorageManager-->>Backend: image_url = "/api/sessions/{id}/photos/user.png"
    else Production環境 (STORAGE_MODE=cloud)
        Backend->>StorageManager: save_file(session_id, "photos/user.png", data)
        StorageManager->>S3: put_object(bucket, key, data)
        S3-->>StorageManager: S3 URL
        StorageManager->>Redis: save_metadata(session_id, "file:photos/user.png", {url})
        StorageManager-->>Backend: image_url = "https://bucket.s3.../..."
    end

    Backend-->>Frontend: {status: success, image_url}
    Frontend-->>User: 画像アップロード完了
```

---

## 6. 画像取得フロー

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Backend
    participant Redis
    participant StorageManager
    participant LocalFS as ローカルFS
    participant S3 as S3/GCS

    User->>Frontend: 画像表示リクエスト
    Frontend->>Backend: GET /api/sessions/{id}/photos/user.png

    rect rgb(255, 240, 200)
        Note over Backend,Redis: セッション確認
        Backend->>Redis: exists(session_id)
        Redis-->>Backend: True
    end

    alt ローカル開発環境
        Backend->>StorageManager: load_file(session_id, "photos/user.png")
        StorageManager->>LocalFS: read from /tmp/user_sessions/{id}/photos/
        LocalFS-->>StorageManager: file_data (bytes)
        StorageManager-->>Backend: file_data
    else Production環境
        Backend->>StorageManager: load_file(session_id, "photos/user.png")
        StorageManager->>S3: get_object(bucket, key)
        S3-->>StorageManager: file_data (bytes)
        StorageManager-->>Backend: file_data
    end

    Backend->>Backend: detect content_type
    Backend-->>Frontend: Response(file_data, mimetype)
    Frontend-->>User: 画像表示
```

---

## 7. 家族エージェント連携フロー

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Backend
    participant FamilySession
    participant Redis
    participant PersonaGenerator
    participant FamilyAgent
    participant Gemini API

    User->>Frontend: セッション完了
    Frontend->>Backend: POST /api/sessions/{id}/complete

    rect rgb(200, 220, 255)
        Note over Backend,Redis: プロファイル読み込み
        Backend->>Redis: load(session_id, "user_profile")
        Redis-->>Backend: profile
        Backend->>Backend: validate profile_is_complete()
    end

    Backend->>FamilySession: new FamilySession(session_id)

    rect rgb(255, 220, 200)
        Note over FamilySession,Redis: キャッシュ読み込み
        FamilySession->>Redis: load(session_id, "family_conversation")
        FamilySession->>Redis: load(session_id, "family_trip_info")
        FamilySession->>Redis: load(session_id, "family_plan")
    end

    Backend->>FamilySession: initialize()
    FamilySession->>PersonaGenerator: generate_personas(profile)
    PersonaGenerator->>Gemini API: Generate Family Personas
    Gemini API-->>PersonaGenerator: personas[]
    PersonaGenerator-->>FamilySession: personas[]
    FamilySession->>FamilySession: build FamilyToolSet

    Backend-->>Frontend: {message: "完了", information_complete: true}

    User->>Frontend: 家族との会話開始
    Frontend->>Backend: POST /api/sessions/{id}/family/messages<br/>{message: "..."}

    Backend->>FamilySession: send_message(user_message)

    loop 各家族メンバー
        FamilySession->>FamilyAgent: family_tool.func(message)
        FamilyAgent->>Gemini API: Generate Response
        Gemini API-->>FamilyAgent: family response
        FamilyAgent-->>FamilySession: {speaker, message}
    end

    rect rgb(200, 255, 200)
        Note over FamilySession,Redis: 会話ログ保存
        FamilySession->>Redis: save(session_id, "family_conversation", log)
        FamilySession->>Redis: save(session_id, "family_trip_info", trip_info)
    end

    FamilySession-->>Backend: replies[]
    Backend-->>Frontend: {reply: replies[], conversation_history}
    Frontend-->>User: 家族メンバーの応答表示
```

---

## 8. Backend/ADK セッション共有フロー

```mermaid
sequenceDiagram
    participant Backend
    participant Redis
    participant ADK

    Note over Backend,ADK: 同じRedisインスタンスを共有

    rect rgb(200, 220, 255)
        Note over Backend,Redis: Backendがデータ保存
        Backend->>Redis: SETEX session:abc:user_profile {...}
        Backend->>Redis: SETEX session:abc:conversation_history [...]
        Redis-->>Backend: OK
    end

    rect rgb(255, 220, 200)
        Note over Redis,ADK: ADKがデータ読み込み
        ADK->>Redis: GET session:abc:user_profile
        Redis-->>ADK: {...}
        ADK->>Redis: GET session:abc:conversation_history
        Redis-->>ADK: [...]
    end

    Note over Backend,ADK: リアルタイムでデータ共有 ✅

    rect rgb(200, 255, 200)
        Note over Redis,ADK: ADKがデータ更新
        ADK->>Redis: SETEX session:abc:debug_info {...}
        Redis-->>ADK: OK
    end

    rect rgb(255, 240, 200)
        Note over Backend,Redis: Backendが更新を確認
        Backend->>Redis: GET session:abc:debug_info
        Redis-->>Backend: {...}
    end
```

---

## 9. データストレージ階層構造

```mermaid
graph TB
    subgraph "セッションデータ (Redis)"
        R1[session:abc:user_profile]
        R2[session:abc:conversation_history]
        R3[session:abc:family_conversation]
        R4[session:abc:family_trip_info]
        R5[session:abc:family_plan]
        R6[session:abc:_meta]
    end

    subgraph "画像データ (ローカル/クラウド)"
        F1[photos/user.png]
        F2[photos/partner.png]
        F3[photos/child_1.png]
    end

    subgraph "メタデータ (Redis - Production)"
        M1[session:abc:meta:file:photos/user.png<br/>{url: s3://...}]
        M2[session:abc:meta:file:photos/partner.png<br/>{url: s3://...}]
    end

    Backend -->|save/load| R1
    Backend -->|save/load| R2
    Backend -->|save/load| R3
    Backend -->|save/load| R4
    Backend -->|save/load| R5

    Backend -->|save/load| F1
    Backend -->|save/load| F2
    Backend -->|save/load| F3

    Backend -.->|Production| M1
    Backend -.->|Production| M2

    style R1 fill:#ff6b6b
    style R2 fill:#ff6b6b
    style R3 fill:#ff6b6b
    style R4 fill:#ff6b6b
    style R5 fill:#ff6b6b
    style R6 fill:#ff6b6b
    style F1 fill:#74b9ff
    style F2 fill:#74b9ff
    style F3 fill:#74b9ff
    style M1 fill:#a29bfe
    style M2 fill:#a29bfe
```

---

## 10. 環境別構成の違い

```mermaid
graph TB
    subgraph "ローカル開発環境"
        LB[Backend]
        LA[ADK]
        LR[(Redis<br/>Container)]
        LF[ファイルシステム<br/>Volume]

        LB -->|セッション| LR
        LA -->|セッション| LR
        LB -->|画像| LF
    end

    subgraph "Production環境"
        PB[Backend<br/>Container]
        PR[(Managed Redis<br/>ElastiCache)]
        PS[(S3/GCS<br/>画像ストレージ)]

        PB -->|セッション| PR
        PB -->|画像| PS
    end

    style LR fill:#ff6b6b
    style LF fill:#74b9ff
    style PR fill:#fd79a8
    style PS fill:#a29bfe
```

---

## 11. エラーハンドリングフロー

```mermaid
flowchart TD
    Start[API リクエスト] --> CheckSession{セッション存在?}

    CheckSession -->|No| Error404[404 Error<br/>セッションが存在しません]
    CheckSession -->|Yes| ValidateInput{入力検証}

    ValidateInput -->|Invalid| Error400[400 Error<br/>不正な入力]
    ValidateInput -->|Valid| ProcessRequest[処理実行]

    ProcessRequest --> RedisOp{Redis操作}
    RedisOp -->|Success| FileOp{ファイル操作}
    RedisOp -->|Fail| Error500Redis[500 Error<br/>Redis接続エラー]

    FileOp -->|Success| Success[200 OK<br/>成功レスポンス]
    FileOp -->|Fail| Error500File[500 Error<br/>ファイル操作エラー]

    Error404 --> Logging[エラーログ記録]
    Error400 --> Logging
    Error500Redis --> Logging
    Error500File --> Logging

    Logging --> Response[エラーレスポンス]
    Success --> Response

    style Error404 fill:#ff6b6b
    style Error400 fill:#ff6b6b
    style Error500Redis fill:#ff6b6b
    style Error500File fill:#ff6b6b
    style Success fill:#51cf66
```

---

## 12. デプロイフロー

```mermaid
flowchart LR
    subgraph "開発"
        Dev[ローカル開発<br/>docker-compose.yml]
        Test[テスト実行<br/>pytest]
    end

    subgraph "ステージング"
        Stage[Redis環境<br/>docker-compose.redis.yml]
        Verify[動作確認]
    end

    subgraph "本番"
        Prod[Production環境<br/>docker-compose.production.yml]
        Monitor[監視・ログ]
    end

    Dev --> Test
    Test -->|Pass| Stage
    Stage --> Verify
    Verify -->|OK| Prod
    Prod --> Monitor
    Monitor -.->|Issue| Dev

    style Dev fill:#95e1d3
    style Test fill:#f9ca24
    style Stage fill:#a29bfe
    style Verify fill:#fd79a8
    style Prod fill:#ff6b6b
    style Monitor fill:#74b9ff
```

---

## 補足説明

### Redis キー構造
```
session:{session_id}:user_profile
session:{session_id}:conversation_history
session:{session_id}:family_conversation
session:{session_id}:family_trip_info
session:{session_id}:family_plan
session:{session_id}:_meta
session:{session_id}:meta:file:photos/{filename}  (Production)
```

### ファイルシステム構造
```
/app/tmp/user_sessions/
  ├── {session_id}/
  │   └── photos/
  │       ├── user.png
  │       ├── partner.png
  │       └── child_1.png
  └── ...
```

### 環境変数による動作切り替え
- `STORAGE_MODE=redis` → セッションはRedis、画像はローカル
- `STORAGE_MODE=cloud` → セッションはRedis、画像はS3/GCS
- `SESSION_TYPE=redis` → Redis使用
- `SESSION_TYPE=file` → ファイルベース（後方互換性）

---

このドキュメントは、実装されたシステムの動作を完全に表現しています。
