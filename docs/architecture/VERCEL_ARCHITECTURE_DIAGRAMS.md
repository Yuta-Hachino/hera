# Vercel アーキテクチャ図

**作成日**: 2025-10-28
**目的**: Vercelデプロイのアーキテクチャを視覚化

---

## 📋 目次

1. [Vercel全体アーキテクチャ](#1-vercel全体アーキテクチャ)
2. [デプロイフロー](#2-デプロイフロー)
3. [リクエストフロー](#3-リクエストフロー)
4. [コスト比較](#4-コスト比較)
5. [AWS ECS vs Vercel](#5-aws-ecs-vs-vercel)
6. [プレビューデプロイ](#6-プレビューデプロイ)
7. [スケーリング](#7-スケーリング)

---

## 1. Vercel全体アーキテクチャ

```mermaid
graph TB
    subgraph "Global Users"
        US[ユーザー<br/>アメリカ]
        EU[ユーザー<br/>ヨーロッパ]
        ASIA[ユーザー<br/>アジア]
    end

    subgraph "Vercel Edge Network（世界100+箇所）"
        Edge_US[Edge Node<br/>San Francisco]
        Edge_EU[Edge Node<br/>Frankfurt]
        Edge_ASIA[Edge Node<br/>Tokyo]
    end

    subgraph "Vercel Platform"
        subgraph "Frontend"
            SSR[Next.js SSR<br/>Server-Side Rendering]
            SSG[Next.js SSG<br/>Static Site Generation]
            ISR[ISR<br/>Incremental Static Regeneration]
        end

        subgraph "Backend（Serverless Functions）"
            API_Auth[API: 認証<br/>/api/auth]
            API_Sessions[API: セッション<br/>/api/sessions]
            API_Messages[API: メッセージ<br/>/api/sessions/[id]/messages]
            API_Agent[API: Agent<br/>/api/agent]
        end

        subgraph "Edge Functions"
            Edge_API[Edge API<br/>超低レイテンシー]
        end
    end

    subgraph "Supabase"
        Auth[Supabase Auth]
        DB[(PostgreSQL<br/>+ RLS)]
        Storage[(Storage)]
        Realtime[Realtime]
    end

    subgraph "External"
        Gemini[Gemini API]
    end

    US -->|HTTPS| Edge_US
    EU -->|HTTPS| Edge_EU
    ASIA -->|HTTPS| Edge_ASIA

    Edge_US --> SSR
    Edge_EU --> SSR
    Edge_ASIA --> SSR

    SSR --> API_Auth
    SSR --> API_Sessions
    SSR --> API_Messages

    API_Auth --> Auth
    API_Sessions --> DB
    API_Messages --> DB
    API_Agent --> Gemini
    API_Agent --> DB

    DB -.->|変更通知| Realtime
    Realtime -.->|WebSocket| SSR

    style Edge_US fill:#000000,color:#ffffff
    style Edge_EU fill:#000000,color:#ffffff
    style Edge_ASIA fill:#000000,color:#ffffff
    style SSR fill:#000000,color:#ffffff
    style Auth fill:#3ecf8e
    style DB fill:#3ecf8e
```

---

## 2. デプロイフロー

```mermaid
sequenceDiagram
    participant Dev as 開発者
    participant Local as ローカル開発
    participant GitHub as GitHub
    participant Vercel as Vercel Build
    participant Edge as Edge Network
    participant User as エンドユーザー

    Note over Dev,User: 開発フロー

    Dev->>Local: npm run dev
    Local-->>Dev: http://localhost:3000

    Dev->>Dev: コード変更
    Dev->>Local: ホットリロード（即座に反映）

    Note over Dev,User: デプロイフロー

    Dev->>GitHub: git push origin main
    GitHub->>Vercel: Webhook（push検出）

    Vercel->>Vercel: 1. ソースコード取得
    Vercel->>Vercel: 2. npm install
    Vercel->>Vercel: 3. next build
    Note right of Vercel: - SSG: 静的HTMLを生成<br/>- API Routes: Serverless Functions化<br/>- 最適化: 画像、CSS、JS圧縮

    Vercel->>Edge: 4. グローバル配信
    Note right of Edge: 世界100+箇所のエッジに配信

    Vercel->>GitHub: 5. デプロイ完了コメント
    Vercel->>Dev: 6. Slack/Email通知

    Note over Dev,User: ユーザーアクセス

    User->>Edge: https://hera.vercel.app
    Edge->>Edge: キャッシュチェック
    Edge-->>User: 超高速レスポンス（10-50ms）
```

---

## 3. リクエストフロー

### 3.1 ページアクセス（SSR）

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant Edge as Edge Network
    participant Vercel as Vercel Function
    participant Supabase as Supabase

    User->>Edge: GET /dashboard
    Edge->>Edge: 認証Cookie確認

    alt Cookie有効
        Edge->>Vercel: Server-Side Rendering
        Vercel->>Supabase: セッション一覧取得
        Supabase-->>Vercel: データ返却
        Vercel->>Vercel: HTMLレンダリング
        Vercel-->>Edge: HTML + データ
        Edge-->>User: 完全なページ表示
    else Cookie無効
        Edge-->>User: 302 Redirect → /login
    end

    Note over User,Supabase: レスポンスタイム: 50-200ms
```

---

### 3.2 APIリクエスト（Serverless Function）

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant Edge as Edge Network
    participant Function as Serverless Function
    participant Supabase as Supabase DB

    User->>Edge: POST /api/sessions
    Note right of User: Header: Authorization: Bearer <JWT>

    Edge->>Function: Function実行
    Function->>Function: JWT検証
    Function->>Supabase: セッション作成<br/>INSERT INTO sessions

    alt 成功
        Supabase-->>Function: 作成完了
        Function-->>Edge: 200 OK + session_id
        Edge-->>User: レスポンス
    else エラー
        Supabase-->>Function: エラー
        Function-->>Edge: 500 Error
        Edge-->>User: エラーメッセージ
    end

    Note over User,Supabase: レスポンスタイム: 100-300ms
```

---

### 3.3 Edge Function（超高速）

```mermaid
graph LR
    subgraph "従来のServerless Function"
        User1[ユーザー<br/>東京] -->|リクエスト| Region1[us-east-1<br/>バージニア]
        Region1 -->|レイテンシー<br/>150ms| User1
    end

    subgraph "Edge Function"
        User2[ユーザー<br/>東京] -->|リクエスト| Edge2[Edge<br/>東京]
        Edge2 -->|レイテンシー<br/>10ms| User2
    end

    style Region1 fill:#ff6b6b
    style Edge2 fill:#51cf66
```

**速度比較**:
- Serverless Function: 100-300ms
- Edge Function: **10-50ms**（最大30倍高速）

---

## 4. コスト比較

```mermaid
graph TB
    subgraph "AWS ECS構成"
        subgraph "月額コスト"
            ECS[ECS Fargate<br/>$30]
            ALB[ALB<br/>$20]
            VPC[VPC/NAT<br/>$30]
            CloudWatch[CloudWatch<br/>$5]
        end

        ECS_Total[合計: $85/月]

        ECS --> ECS_Total
        ALB --> ECS_Total
        VPC --> ECS_Total
        CloudWatch --> ECS_Total
    end

    subgraph "Vercel構成"
        subgraph "月額コスト"
            Vercel_Hobby[Vercel Hobby<br/>$0]
            Vercel_Pro[Vercel Pro<br/>$20]
        end

        Vercel_Total_Hobby[合計: $0/月]
        Vercel_Total_Pro[合計: $20/月]

        Vercel_Hobby --> Vercel_Total_Hobby
        Vercel_Pro --> Vercel_Total_Pro
    end

    subgraph "+ Supabase"
        Supabase[Supabase Pro<br/>$25/月]
    end

    subgraph "最終コスト"
        Final_ECS[AWS: $110/月<br/>$1,320/年]
        Final_Hobby[Vercel Hobby: $25/月<br/>$300/年]
        Final_Pro[Vercel Pro: $45/月<br/>$540/年]
    end

    ECS_Total --> Final_ECS
    Supabase --> Final_ECS

    Vercel_Total_Hobby --> Final_Hobby
    Supabase --> Final_Hobby

    Vercel_Total_Pro --> Final_Pro
    Supabase --> Final_Pro

    Savings_Hobby[削減額:<br/>$1,020/年<br/>77%削減]
    Savings_Pro[削減額:<br/>$780/年<br/>59%削減]

    Final_ECS -.->|比較| Savings_Hobby
    Final_Hobby -.->|比較| Savings_Hobby

    Final_ECS -.->|比較| Savings_Pro
    Final_Pro -.->|比較| Savings_Pro

    style ECS_Total fill:#ff6b6b
    style Vercel_Total_Hobby fill:#51cf66
    style Vercel_Total_Pro fill:#51cf66
    style Savings_Hobby fill:#ffd43b
    style Savings_Pro fill:#ffd43b
```

---

## 5. AWS ECS vs Vercel

```mermaid
graph LR
    subgraph "AWS ECS"
        subgraph "セットアップ"
            A1[Terraformコード<br/>8時間]
            A2[VPC設定<br/>2時間]
            A3[ECS設定<br/>3時間]
            A4[ALB設定<br/>2時間]
        end

        A_Time[合計: 15時間]

        A1 --> A_Time
        A2 --> A_Time
        A3 --> A_Time
        A4 --> A_Time
    end

    subgraph "Vercel"
        subgraph "セットアップ"
            B1[GitHub連携<br/>5分]
            B2[環境変数設定<br/>10分]
            B3[デプロイ<br/>5分]
        end

        B_Time[合計: 20分]

        B1 --> B_Time
        B2 --> B_Time
        B3 --> B_Time
    end

    Comparison[時間削減:<br/>14時間40分<br/>98%削減]

    A_Time -.->|比較| Comparison
    B_Time -.->|比較| Comparison

    style A_Time fill:#ff6b6b
    style B_Time fill:#51cf66
    style Comparison fill:#ffd43b
```

---

### 機能比較マトリクス

```mermaid
graph TB
    subgraph "比較項目"
        subgraph "AWS ECS"
            ECS_Cost[月額コスト<br/>$85]
            ECS_Setup[セットアップ<br/>15時間]
            ECS_Deploy[デプロイ時間<br/>3-5分]
            ECS_Scale[スケーリング<br/>手動設定]
            ECS_CDN[CDN<br/>別途CloudFront]
            ECS_SSL[HTTPS<br/>ACM設定必要]
        end

        subgraph "Vercel"
            V_Cost[月額コスト<br/>$0-$20]
            V_Setup[セットアップ<br/>20分]
            V_Deploy[デプロイ時間<br/>30秒]
            V_Scale[スケーリング<br/>自動無限]
            V_CDN[CDN<br/>標準装備]
            V_SSL[HTTPS<br/>自動]
        end
    end

    ECS_Cost -.->|比較| V_Cost
    ECS_Setup -.->|比較| V_Setup
    ECS_Deploy -.->|比較| V_Deploy
    ECS_Scale -.->|比較| V_Scale
    ECS_CDN -.->|比較| V_CDN
    ECS_SSL -.->|比較| V_SSL

    style ECS_Cost fill:#ff6b6b
    style ECS_Setup fill:#ff6b6b
    style ECS_Deploy fill:#ff6b6b
    style ECS_Scale fill:#ff6b6b
    style ECS_CDN fill:#ff6b6b
    style ECS_SSL fill:#ff6b6b

    style V_Cost fill:#51cf66
    style V_Setup fill:#51cf66
    style V_Deploy fill:#51cf66
    style V_Scale fill:#51cf66
    style V_CDN fill:#51cf66
    style V_SSL fill:#51cf66
```

---

## 6. プレビューデプロイ

```mermaid
sequenceDiagram
    participant Dev as 開発者
    participant Branch as feature/new-feature
    participant GitHub as GitHub
    participant Vercel as Vercel
    participant Team as チームメンバー

    Note over Dev,Team: Pull Request作成

    Dev->>Branch: git checkout -b feature/new-feature
    Dev->>Branch: コード変更
    Dev->>GitHub: git push origin feature/new-feature
    GitHub->>GitHub: Pull Request作成

    Note over Dev,Team: 自動プレビュービルド

    GitHub->>Vercel: Webhook（PR検出）
    Vercel->>Vercel: プレビュービルド
    Note right of Vercel: 独立した環境<br/>本番に影響なし

    Vercel->>GitHub: プレビューURL投稿
    Note right of GitHub: https://hera-git-feature-new-feature.vercel.app

    GitHub->>Team: PR通知（Slack）

    Note over Dev,Team: レビュー

    Team->>GitHub: プレビューURLにアクセス
    GitHub->>Vercel: プレビュー環境
    Vercel-->>Team: 実際の動作確認

    Team->>GitHub: レビューコメント
    Dev->>Branch: 修正
    Dev->>GitHub: git push

    Note over Dev,Team: 自動再ビルド

    GitHub->>Vercel: 新しいコミット検出
    Vercel->>Vercel: プレビュー再ビルド
    Vercel->>GitHub: 更新完了

    Note over Dev,Team: マージ

    Team->>GitHub: Approve & Merge
    GitHub->>Vercel: main ブランチデプロイ
    Vercel->>Vercel: 本番デプロイ
    Vercel->>Team: 本番デプロイ完了通知
```

**メリット**:
- ✅ PR毎に独立した環境
- ✅ 本番に影響なし
- ✅ チーム全員が実際の動作確認
- ✅ レビューが容易

---

## 7. スケーリング

### 7.1 AWS ECS のスケーリング

```mermaid
graph TB
    subgraph "手動スケーリング設定"
        Config[ECS設定]
        CPU[CPU閾値<br/>70%]
        Scale_Out[スケールアウト<br/>タスク追加]
        Scale_In[スケールイン<br/>タスク削減]

        Config --> CPU
        CPU -->|超過| Scale_Out
        CPU -->|低下| Scale_In
    end

    subgraph "制約"
        Limit1[最大タスク数<br/>制限あり]
        Limit2[起動時間<br/>30-60秒]
        Limit3[コスト<br/>常時課金]
    end

    Scale_Out -.-> Limit1
    Scale_Out -.-> Limit2
    Scale_Out -.-> Limit3

    style Config fill:#ff6b6b
    style Limit1 fill:#ff6b6b
    style Limit2 fill:#ff6b6b
    style Limit3 fill:#ff6b6b
```

---

### 7.2 Vercel の自動スケーリング

```mermaid
graph TB
    subgraph "完全自動スケーリング"
        Request[リクエスト]
        Auto[Vercel Auto Scale]
        Infinite[無限スケール]

        Request -->|増加| Auto
        Auto -->|即座に| Infinite
    end

    subgraph "メリット"
        Instant[起動時間<br/>0秒（コールドスタートなし）]
        NoLimit[上限<br/>なし]
        PayPerUse[課金<br/>使った分だけ]
    end

    Infinite --> Instant
    Infinite --> NoLimit
    Infinite --> PayPerUse

    style Auto fill:#51cf66
    style Infinite fill:#51cf66
    style Instant fill:#51cf66
    style NoLimit fill:#51cf66
    style PayPerUse fill:#51cf66
```

**トラフィック急増時の対応**:

| 項目 | AWS ECS | Vercel |
|------|---------|--------|
| **スケール時間** | 30-60秒 | **即座（0秒）** |
| **上限** | 設定した最大タスク数 | **無制限** |
| **設定** | 複雑（Auto Scaling設定） | **不要** |
| **コスト** | タスク数 × 時間 | **実行時間のみ** |

---

### 7.3 トラフィックシミュレーション

```mermaid
graph TB
    subgraph "通常時（100 req/min）"
        Normal_ECS[ECS: 2タスク<br/>$30/月]
        Normal_Vercel[Vercel: 自動<br/>$0-$20/月]
    end

    subgraph "ピーク時（10,000 req/min）"
        Peak_ECS[ECS: 20タスク<br/>$300/月]
        Peak_Vercel[Vercel: 自動<br/>$20-$40/月]
    end

    subgraph "バズ時（100,000 req/min）"
        Viral_ECS[ECS: 上限到達<br/>サービス停止リスク]
        Viral_Vercel[Vercel: 無限スケール<br/>$40-$100/月]
    end

    Normal_ECS --> Peak_ECS
    Peak_ECS --> Viral_ECS

    Normal_Vercel --> Peak_Vercel
    Peak_Vercel --> Viral_Vercel

    style Viral_ECS fill:#ff6b6b
    style Viral_Vercel fill:#51cf66
```

**結論**: Vercelは急激なトラフィック増加にも対応可能

---

## 8. 開発体験（DX）

```mermaid
graph LR
    subgraph "AWS ECS"
        subgraph "開発フロー"
            E1[ローカル開発]
            E2[Dockerビルド<br/>5-10分]
            E3[ECRプッシュ<br/>3-5分]
            E4[ECSデプロイ<br/>3-5分]
            E5[動作確認]
        end

        E_Time[合計: 15-25分]

        E1 --> E2
        E2 --> E3
        E3 --> E4
        E4 --> E5
        E5 -.-> E_Time
    end

    subgraph "Vercel"
        subgraph "開発フロー"
            V1[ローカル開発]
            V2[git push]
            V3[自動デプロイ<br/>30秒]
            V4[動作確認]
        end

        V_Time[合計: 30秒]

        V1 --> V2
        V2 --> V3
        V3 --> V4
        V4 -.-> V_Time
    end

    Compare[開発速度:<br/>30-50倍高速]

    E_Time -.->|比較| Compare
    V_Time -.->|比較| Compare

    style E_Time fill:#ff6b6b
    style V_Time fill:#51cf66
    style Compare fill:#ffd43b
```

---

## 9. 監視・ログ

### 9.1 Vercel Analytics（標準装備）

```mermaid
graph TB
    subgraph "Vercel Dashboard"
        Analytics[Analytics<br/>リアルタイム]
        Logs[ログ<br/>自動収集]
        Metrics[メトリクス<br/>パフォーマンス]
    end

    subgraph "自動収集データ"
        PageViews[ページビュー]
        Performance[Core Web Vitals]
        Errors[エラー率]
        Latency[レイテンシー]
        Geographic[地域別アクセス]
    end

    Analytics --> PageViews
    Analytics --> Performance
    Logs --> Errors
    Metrics --> Latency
    Metrics --> Geographic

    style Analytics fill:#51cf66
    style Logs fill:#51cf66
    style Metrics fill:#51cf66
```

**追加設定不要**: 全て標準で含まれる

---

### 9.2 AWS ECS 監視（別途設定必要）

```mermaid
graph TB
    subgraph "CloudWatch設定"
        CW[CloudWatch<br/>手動設定]
        Alarms[Alarms<br/>閾値設定]
        Logs[Logs<br/>ログ転送設定]
    end

    subgraph "追加コスト"
        Cost1[ログ保存<br/>$5/月]
        Cost2[メトリクス<br/>$3/月]
        Cost3[Alarms<br/>$1/月]
    end

    CW --> Cost1
    Alarms --> Cost2
    Logs --> Cost3

    Total[合計: $9/月]

    Cost1 --> Total
    Cost2 --> Total
    Cost3 --> Total

    style CW fill:#ff6b6b
    style Total fill:#ff6b6b
```

**Vercel**: $0（標準装備）
**AWS ECS**: $9/月（別途設定）

---

## 10. まとめ

### ✅ Vercel の圧倒的なメリット

| 項目 | AWS ECS | Vercel | 改善率 |
|------|---------|--------|--------|
| **月額コスト** | $85 | $0-$20 | **-76% - -100%** |
| **セットアップ** | 15時間 | 20分 | **-98%** |
| **デプロイ時間** | 3-5分 | 30秒 | **-90%** |
| **スケーリング** | 手動 | 自動無限 | ✅ |
| **CDN** | 別途 | 標準 | ✅ |
| **プレビュー** | なし | 自動 | ✅ |
| **監視** | $9/月 | $0 | **-100%** |

### 🎯 推奨

**Vercelを使うべき理由**:

1. **コスト**: 年間$780-$1,020削減
2. **速度**: デプロイ30倍高速
3. **簡単**: セットアップ98%削減
4. **スケール**: 無限自動スケーリング
5. **DX**: 圧倒的な開発体験

**AWS ECSを使うべきケース**:
- ❌ ほぼない（Vercelで十分）

---

**Vercelで、最高のHeraを構築しましょう！**
