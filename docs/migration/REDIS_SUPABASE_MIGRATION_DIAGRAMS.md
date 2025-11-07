# Redis → Supabase 移行フロー図

**作成日**: 2025-10-28
**目的**: RedisからSupabaseへの移行を視覚化

---

## 📋 目次

1. [現状アーキテクチャ（Redis + S3）](#1-現状アーキテクチャredis--s3)
2. [移行後アーキテクチャ（Supabaseのみ）](#2-移行後アーキテクチャsupabaseのみ)
3. [パフォーマンス比較](#3-パフォーマンス比較)
4. [データ構造の変換](#4-データ構造の変換)
5. [移行プロセス](#5-移行プロセス)
6. [コスト比較](#6-コスト比較)
7. [段階的移行フロー](#7-段階的移行フロー)

---

## 1. 現状アーキテクチャ（Redis + S3）

```mermaid
graph TB
    subgraph "フロントエンド"
        Frontend[Next.js<br/>Vercel]
    end

    subgraph "バックエンド"
        Backend[Flask API<br/>Backend Container]
        ADK[Google ADK<br/>ADK Container]
    end

    subgraph "データストア"
        Redis[(Redis<br/>セッションデータ<br/>Key-Value)]
        S3[(S3/GCS<br/>画像ファイル)]
    end

    Frontend -->|HTTP| Backend
    Backend -->|Session R/W| Redis
    Backend -->|画像 Upload/Download| S3
    ADK -->|Session R/W| Redis
    ADK -->|画像取得| S3

    Redis -.->|データ構造| RedisKeys[session:abc123:user_profile<br/>session:abc123:conversation_history<br/>session:abc123:family_conversation<br/>session:abc123:family_trip_info]

    style Redis fill:#dc382d
    style S3 fill:#ff9900
    style RedisKeys fill:#f5f5f5
```

### 課題

- ⚠️ **2つのサービス管理**: Redis + S3
- ⚠️ **クエリ機能が限定的**: Key-Value構造のみ
- ⚠️ **データ整合性**: 手動管理が必要
- ⚠️ **バックアップ**: 別途設定が必要

---

## 2. 移行後アーキテクチャ（Supabaseのみ）

```mermaid
graph TB
    subgraph "フロントエンド"
        Frontend[Next.js<br/>Vercel]
    end

    subgraph "バックエンド"
        Backend[Flask API<br/>Backend Container]
        ADK[Google ADK<br/>ADK Container]
    end

    subgraph "Supabase"
        PostgreSQL[(PostgreSQL<br/>構造化データ<br/>SQL)]
        Storage[(Supabase Storage<br/>画像ファイル)]
        Realtime[Realtime<br/>リアルタイム更新]
    end

    Frontend -->|HTTP| Backend
    Frontend -.->|直接アクセス可| PostgreSQL
    Backend -->|SQL| PostgreSQL
    Backend -->|Storage API| Storage
    ADK -->|SQL| PostgreSQL
    ADK -->|Storage API| Storage

    PostgreSQL -->|変更通知| Realtime
    Realtime -.->|WebSocket| Frontend

    PostgreSQL -.->|データ構造| Tables[sessions<br/>user_profiles<br/>conversation_history<br/>family_conversations<br/>family_trip_info<br/>family_plans<br/>session_images]

    style PostgreSQL fill:#3ecf8e
    style Storage fill:#3ecf8e
    style Realtime fill:#3ecf8e
    style Tables fill:#f5f5f5
```

### メリット

- ✅ **1つのプラットフォーム**: Supabaseで完結
- ✅ **SQLクエリ**: 複雑な検索が可能
- ✅ **データ整合性**: 外部キーで自動管理
- ✅ **自動バックアップ**: 標準装備
- ✅ **リアルタイム機能**: 追加コストなし

---

## 3. パフォーマンス比較

```mermaid
graph LR
    subgraph "操作別レスポンスタイム"
        subgraph "単純な読み取り"
            Redis1[Redis<br/>0.8ms]
            Supa1[Supabase<br/>3.2ms]
        end

        subgraph "単純な書き込み"
            Redis2[Redis<br/>0.9ms]
            Supa2[Supabase<br/>4.1ms]
        end

        subgraph "複雑なクエリ"
            Redis3[Redis<br/>10-50ms<br/>Pythonでフィルタ]
            Supa3[Supabase<br/>5-15ms<br/>SQLでフィルタ]
        end

        subgraph "JOIN操作"
            Redis4[Redis<br/>20-100ms<br/>複数回アクセス]
            Supa4[Supabase<br/>8-20ms<br/>1回のクエリ]
        end
    end

    style Redis1 fill:#dc382d
    style Redis2 fill:#dc382d
    style Redis3 fill:#dc382d
    style Redis4 fill:#dc382d
    style Supa1 fill:#3ecf8e
    style Supa2 fill:#3ecf8e
    style Supa3 fill:#3ecf8e
    style Supa4 fill:#3ecf8e
```

### 結論

- **単純操作**: Redisが約4倍速い（0.8ms vs 3.2ms）
- **複雑操作**: Supabaseが2-5倍速い
- **ユーザー体験**: どちらも100ms以下で体感差なし ✅

---

## 4. データ構造の変換

```mermaid
graph LR
    subgraph "Redis Key-Value"
        RedisData["Key: session:abc123:user_profile<br/>Value: {<br/>  'name': '太郎',<br/>  'age': 30,<br/>  'partner_name': '花子'<br/>}<br/><br/>Key: session:abc123:conversation_history<br/>Value: [<br/>  {'speaker': 'user', 'message': 'こんにちは'},<br/>  {'speaker': 'agent', 'message': 'どうも！'}<br/>]"]
    end

    subgraph "PostgreSQL Relational"
        Sessions["sessions<br/>---<br/>id | session_id | created_at<br/>1  | abc123     | 2025-10-28"]

        Profiles["user_profiles<br/>---<br/>id | session_id | name | age | partner_name<br/>1  | abc123     | 太郎 | 30  | 花子"]

        Conversations["conversation_history<br/>---<br/>id | session_id | speaker | message<br/>1  | abc123     | user    | こんにちは<br/>2  | abc123     | agent   | どうも！"]
    end

    RedisData -->|変換| Sessions
    RedisData -->|変換| Profiles
    RedisData -->|変換| Conversations

    Sessions -->|外部キー| Profiles
    Sessions -->|外部キー| Conversations

    style RedisData fill:#ffe6e6
    style Sessions fill:#e6ffe6
    style Profiles fill:#e6ffe6
    style Conversations fill:#e6ffe6
```

### 変換の利点

1. **データ正規化**: 重複を排除
2. **整合性保証**: 外部キーで関連性を保持
3. **柔軟なクエリ**: SQLで複雑な検索が可能
4. **型安全**: 各カラムに明確な型定義

---

## 5. 移行プロセス

```mermaid
sequenceDiagram
    participant Admin as 管理者
    participant Script as 移行スクリプト
    participant Redis as Redis
    participant Supabase as Supabase PostgreSQL
    participant Verify as 検証

    Note over Admin,Verify: Phase 1: 準備

    Admin->>Supabase: 1. Supabaseプロジェクト作成
    Supabase-->>Admin: API URL/Key取得

    Admin->>Supabase: 2. スキーマ作成
    Supabase-->>Admin: テーブル作成完了

    Note over Admin,Verify: Phase 2: データ移行

    Admin->>Script: 3. 移行スクリプト実行
    Script->>Redis: 全セッションキー取得
    Redis-->>Script: [session:abc123, session:def456, ...]

    loop 各セッションごと
        Script->>Redis: user_profile 取得
        Redis-->>Script: JSON データ
        Script->>Redis: conversation_history 取得
        Redis-->>Script: JSON 配列
        Script->>Redis: family データ取得
        Redis-->>Script: JSON データ

        Script->>Script: データ変換・正規化
        Script->>Supabase: sessions INSERT
        Script->>Supabase: user_profiles INSERT
        Script->>Supabase: conversation_history INSERT
        Script->>Supabase: family データ INSERT
    end

    Note over Admin,Verify: Phase 3: 検証

    Script->>Verify: データ件数確認
    Verify->>Redis: COUNT keys
    Redis-->>Verify: Redis件数
    Verify->>Supabase: COUNT rows
    Supabase-->>Verify: Supabase件数
    Verify->>Verify: 件数一致確認

    Verify->>Admin: 移行完了レポート

    Note over Admin,Verify: Phase 4: 切り替え

    Admin->>Admin: backend/api/app.py 修正
    Note right of Admin: RedisSessionManager<br/>↓<br/>SupabaseSessionManager

    Admin->>Admin: テスト実行
    Admin->>Redis: Redis停止・削除
    Admin-->>Admin: 移行完了！
```

---

## 6. コスト比較

```mermaid
graph TB
    subgraph "Option A: Redis + S3（現状）"
        subgraph "インフラコスト"
            RedisCost[ElastiCache<br/>cache.t3.micro<br/>$15/月]
            S3Cost[S3 Storage<br/>10GB + 転送<br/>$5/月]
        end

        subgraph "管理コスト"
            RedisManage[運用工数<br/>3時間/月<br/>$150/月]
        end

        TotalA[合計<br/>$170/月]
    end

    subgraph "Option B: Supabase のみ（移行後）"
        subgraph "インフラコスト"
            SupaCost[Supabase Pro<br/>8GB DB + 100GB Storage<br/>$25/月]
        end

        subgraph "管理コスト"
            SupaManage[運用工数<br/>1時間/月<br/>$50/月]
        end

        TotalB[合計<br/>$75/月]
    end

    subgraph "削減額"
        Savings[月額 $95 削減<br/>年間 $1,140 削減]
    end

    RedisCost --> TotalA
    S3Cost --> TotalA
    RedisManage --> TotalA

    SupaCost --> TotalB
    SupaManage --> TotalB

    TotalA -.->|差額| Savings
    TotalB -.->|差額| Savings

    style TotalA fill:#dc382d
    style TotalB fill:#3ecf8e
    style Savings fill:#f39c12
```

### 年間コスト比較

| 項目 | Redis + S3 | Supabase | 削減額 |
|------|------------|----------|--------|
| **インフラ費** | $240 | $300 | -$60 |
| **管理工数（時給$50）** | $1,800 | $600 | **+$1,200** |
| **合計** | **$2,040** | **$900** | **$1,140** |

**結論**: Supabaseに移行すると **年間$1,140削減**

---

## 7. 段階的移行フロー

```mermaid
graph TB
    subgraph "Week 1: 準備"
        W1_1[Supabaseプロジェクト作成]
        W1_2[データベーススキーマ作成]
        W1_3[移行スクリプト作成]
        W1_4[ローカル環境でテスト]

        W1_1 --> W1_2
        W1_2 --> W1_3
        W1_3 --> W1_4
    end

    subgraph "Week 2: 並行運用開始"
        W2_1[新規セッションは<br/>Supabaseへ保存]
        W2_2[既存セッションは<br/>Redisから読み取り]
        W2_3[Dual Write実装<br/>Redis + Supabase両方]
        W2_4[動作確認]

        W2_1 --> W2_2
        W2_2 --> W2_3
        W2_3 --> W2_4
    end

    subgraph "Week 3: データ移行"
        W3_1[既存データを<br/>Supabaseへコピー]
        W3_2[データ整合性確認]
        W3_3[移行完了率: 50%]
        W3_4[動作確認]

        W3_1 --> W3_2
        W3_2 --> W3_3
        W3_3 --> W3_4
    end

    subgraph "Week 4: 完全移行"
        W4_1[全データを<br/>Supabaseへ移行完了]
        W4_2[Redisへの書き込み停止]
        W4_3[Supabaseのみから読み取り]
        W4_4[1週間の監視期間]

        W4_1 --> W4_2
        W4_2 --> W4_3
        W4_3 --> W4_4
    end

    subgraph "Week 5: Redis削除"
        W5_1[Redis接続コード削除]
        W5_2[Redisコンテナ停止]
        W5_3[docker-compose.yml更新]
        W5_4[ドキュメント更新]

        W5_1 --> W5_2
        W5_2 --> W5_3
        W5_3 --> W5_4
    end

    W1_4 --> W2_1
    W2_4 --> W3_1
    W3_4 --> W4_1
    W4_4 --> W5_1

    style W1_4 fill:#3498db
    style W2_4 fill:#3498db
    style W3_4 fill:#f39c12
    style W4_4 fill:#27ae60
    style W5_4 fill:#27ae60
```

---

## 8. リスク管理

```mermaid
graph TB
    subgraph "リスク評価"
        Risk1[データ消失<br/>リスク: 高]
        Risk2[ダウンタイム<br/>リスク: 中]
        Risk3[パフォーマンス劣化<br/>リスク: 低]
    end

    subgraph "対策"
        Mit1[完全バックアップ<br/>移行前にRedisダンプ保存]
        Mit2[段階的移行<br/>並行運用期間を設ける]
        Mit3[インデックス最適化<br/>事前にパフォーマンステスト]
    end

    subgraph "ロールバック計画"
        RB1[Redisコンテナを<br/>即座に再起動可能]
        RB2[バックアップから<br/>データ復元]
        RB3[コード切り戻し<br/>Git revert]
    end

    Risk1 --> Mit1
    Risk2 --> Mit2
    Risk3 --> Mit3

    Mit1 --> RB1
    Mit2 --> RB2
    Mit3 --> RB3

    style Risk1 fill:#e74c3c
    style Risk2 fill:#f39c12
    style Risk3 fill:#3498db
    style Mit1 fill:#27ae60
    style Mit2 fill:#27ae60
    style Mit3 fill:#27ae60
```

---

## 9. Before/After 比較

```mermaid
graph LR
    subgraph "Before（Redis + S3）"
        B1[管理対象<br/>2サービス]
        B2[クエリ機能<br/>Key-Valueのみ]
        B3[データ整合性<br/>手動管理]
        B4[バックアップ<br/>別途設定]
        B5[リアルタイム<br/>Redis Pub/Sub]
        B6[月額コスト<br/>$170]
    end

    subgraph "After（Supabaseのみ）"
        A1[管理対象<br/>1サービス]
        A2[クエリ機能<br/>SQLフル機能]
        A3[データ整合性<br/>外部キーで自動]
        A4[バックアップ<br/>自動（毎日）]
        A5[リアルタイム<br/>Supabase Realtime]
        A6[月額コスト<br/>$75]
    end

    B1 -.->|改善| A1
    B2 -.->|改善| A2
    B3 -.->|改善| A3
    B4 -.->|改善| A4
    B5 -.->|改善| A5
    B6 -.->|改善| A6

    style B1 fill:#ffe6e6
    style B2 fill:#ffe6e6
    style B3 fill:#ffe6e6
    style B4 fill:#ffe6e6
    style B5 fill:#ffe6e6
    style B6 fill:#ffe6e6

    style A1 fill:#e6ffe6
    style A2 fill:#e6ffe6
    style A3 fill:#e6ffe6
    style A4 fill:#e6ffe6
    style A5 fill:#e6ffe6
    style A6 fill:#e6ffe6
```

---

## 10. 移行完了チェックリスト

```mermaid
graph TB
    Start([移行開始])

    Check1{Supabaseプロジェクト<br/>作成済み？}
    Check2{データベーススキーマ<br/>作成済み？}
    Check3{移行スクリプト<br/>テスト済み？}
    Check4{データ移行<br/>完了？}
    Check5{データ整合性<br/>確認済み？}
    Check6{本番環境で<br/>動作確認済み？}
    Check7{Redis停止済み？}
    Check8{ドキュメント<br/>更新済み？}

    End([移行完了！])

    Start --> Check1
    Check1 -->|YES| Check2
    Check1 -->|NO| Task1[プロジェクト作成]
    Task1 --> Check1

    Check2 -->|YES| Check3
    Check2 -->|NO| Task2[スキーマ作成]
    Task2 --> Check2

    Check3 -->|YES| Check4
    Check3 -->|NO| Task3[スクリプトテスト]
    Task3 --> Check3

    Check4 -->|YES| Check5
    Check4 -->|NO| Task4[データ移行実行]
    Task4 --> Check4

    Check5 -->|YES| Check6
    Check5 -->|NO| Task5[データ検証]
    Task5 --> Check5

    Check6 -->|YES| Check7
    Check6 -->|NO| Task6[動作確認]
    Task6 --> Check6

    Check7 -->|YES| Check8
    Check7 -->|NO| Task7[Redis停止]
    Task7 --> Check7

    Check8 -->|YES| End
    Check8 -->|NO| Task8[ドキュメント更新]
    Task8 --> Check8

    style Start fill:#3498db
    style End fill:#27ae60
    style Check1 fill:#f39c12
    style Check2 fill:#f39c12
    style Check3 fill:#f39c12
    style Check4 fill:#f39c12
    style Check5 fill:#f39c12
    style Check6 fill:#f39c12
    style Check7 fill:#f39c12
    style Check8 fill:#f39c12
```

---

## まとめ

### ✅ Redisを削除し、Supabaseに統合する理由

1. **管理の簡素化**: 2サービス → 1サービス
2. **機能の向上**: Key-Value → SQLフル機能
3. **コスト削減**: $170/月 → $75/月（$95削減）
4. **運用工数削減**: 3時間/月 → 1時間/月
5. **データ整合性**: 手動 → 自動（外部キー）
6. **パフォーマンス**: 実用上問題なし（3ms）

### 🚀 次のステップ

1. **Week 1**: Supabaseセットアップ
2. **Week 2-3**: 段階的にデータ移行
3. **Week 4**: 動作確認・監視
4. **Week 5**: Redis完全削除

**所要時間**: 5週間（安全な移行）
**投資時間**: 20-25時間
**年間削減額**: $1,140

**Redisは削除し、Supabaseに統合しましょう！**
