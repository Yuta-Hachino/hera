# Terraform アーキテクチャ図

**作成日**: 2025-10-28
**対象**: HeraプロジェクトのTerraform構成を視覚化

---

## 📋 目次

1. [Terraform全体構成](#1-terraform全体構成)
2. [モジュール構造](#2-モジュール構造)
3. [環境別デプロイフロー](#3-環境別デプロイフロー)
4. [AWSインフラ構成](#4-awsインフラ構成)
5. [Supabase管理フロー](#5-supabase管理フロー)
6. [CI/CDパイプライン](#6-cicdパイプライン)
7. [状態管理](#7-状態管理)
8. [開発フロー](#8-開発フロー)
9. [環境間の差異](#9-環境間の差異)
10. [コスト最適化フロー](#10-コスト最適化フロー)

---

## 1. Terraform全体構成

```mermaid
graph TB
    subgraph "開発者"
        Dev[開発者<br/>コード変更]
    end

    subgraph "Git Repository"
        GitRepo[GitHub<br/>terraform/]
    end

    subgraph "CI/CD"
        Actions[GitHub Actions<br/>terraform workflow]
    end

    subgraph "Terraform State"
        S3State[(S3 Bucket<br/>terraform.tfstate)]
        DynamoDB[(DynamoDB<br/>State Lock)]
    end

    subgraph "Terraform Modules"
        NetworkMod[Networking<br/>Module]
        SupabaseMod[Supabase<br/>Module]
        ECSMod[ECS<br/>Module]
    end

    subgraph "クラウドリソース"
        subgraph "Supabase"
            SupaDB[(PostgreSQL)]
            SupaStorage[(Storage)]
            SupaRLS[RLS Policies]
        end

        subgraph "AWS"
            VPC[VPC]
            ECS[ECS Cluster]
            ALB[Application LB]
        end
    end

    Dev --> GitRepo
    GitRepo --> Actions
    Actions --> S3State
    Actions --> DynamoDB
    Actions --> NetworkMod
    Actions --> SupabaseMod
    Actions --> ECSMod

    NetworkMod --> VPC
    SupabaseMod --> SupaDB
    SupabaseMod --> SupaStorage
    SupabaseMod --> SupaRLS
    ECSMod --> ECS
    ECSMod --> ALB

    style SupaDB fill:#3ecf8e
    style SupaStorage fill:#3ecf8e
    style SupaRLS fill:#3ecf8e
    style S3State fill:#ff9900
    style DynamoDB fill:#ff9900
```

---

## 2. モジュール構造

```mermaid
graph LR
    subgraph "terraform/"
        subgraph "modules/"
            NetMod[networking/<br/>VPC, Subnet, IGW]
            SupaMod[supabase/<br/>DB, Storage, RLS]
            ECSMod[ecs/<br/>Cluster, Task, Service]
            MonMod[monitoring/<br/>CloudWatch, Alarms]
        end

        subgraph "environments/"
            DevEnv[dev/<br/>main.tf]
            StagingEnv[staging/<br/>main.tf]
            ProdEnv[prod/<br/>main.tf]
        end

        Providers[providers.tf<br/>AWS, Supabase]
        Variables[variables.tf<br/>共通変数]
        Outputs[outputs.tf<br/>出力値]
    end

    DevEnv --> NetMod
    DevEnv --> SupaMod
    DevEnv --> ECSMod
    DevEnv --> MonMod

    StagingEnv --> NetMod
    StagingEnv --> SupaMod
    StagingEnv --> ECSMod
    StagingEnv --> MonMod

    ProdEnv --> NetMod
    ProdEnv --> SupaMod
    ProdEnv --> ECSMod
    ProdEnv --> MonMod

    DevEnv --> Providers
    StagingEnv --> Providers
    ProdEnv --> Providers

    style NetMod fill:#4a90e2
    style SupaMod fill:#3ecf8e
    style ECSMod fill:#ff9900
    style MonMod fill:#f39c12
```

---

## 3. 環境別デプロイフロー

```mermaid
sequenceDiagram
    participant Dev as 開発者
    participant Git as GitHub
    participant TFPlan as Terraform Plan
    participant Review as レビュー
    participant TFApply as Terraform Apply
    participant Infra as インフラ

    Note over Dev,Infra: Development 環境
    Dev->>Git: git push (terraform/environments/dev)
    Git->>TFPlan: GitHub Actions トリガー
    TFPlan->>TFPlan: terraform plan
    TFPlan->>TFApply: 自動承認
    TFApply->>Infra: terraform apply（自動）
    Infra-->>Dev: デプロイ完了

    Note over Dev,Infra: Production 環境
    Dev->>Git: Pull Request (terraform/environments/prod)
    Git->>TFPlan: GitHub Actions トリガー
    TFPlan->>TFPlan: terraform plan
    TFPlan->>Review: プラン結果をPRにコメント
    Review->>Review: 人間によるレビュー
    Review->>Git: PR承認・マージ
    Git->>TFApply: GitHub Actions トリガー
    TFApply->>Infra: terraform apply（手動承認）
    Infra-->>Dev: デプロイ完了通知（Slack）
```

---

## 4. AWSインフラ構成

```mermaid
graph TB
    subgraph "Terraform管理対象"
        TF[Terraform<br/>ECS Module]
    end

    subgraph "AWS Region: ap-northeast-1"
        subgraph "VPC: 10.0.0.0/16"
            subgraph "Public Subnets"
                PubSub1[10.0.0.0/24<br/>AZ-1a]
                PubSub2[10.0.1.0/24<br/>AZ-1c]
            end

            subgraph "Private Subnets"
                PrivSub1[10.0.10.0/24<br/>AZ-1a]
                PrivSub2[10.0.11.0/24<br/>AZ-1c]
            end

            IGW[Internet<br/>Gateway]
            NAT1[NAT Gateway<br/>AZ-1a]
            NAT2[NAT Gateway<br/>AZ-1c]

            subgraph "Public Load Balancer"
                ALB[Application LB<br/>https://api.hera.com]
            end

            subgraph "ECS Cluster"
                subgraph "Backend Service"
                    Task1[Backend Task 1<br/>10.0.10.10]
                    Task2[Backend Task 2<br/>10.0.10.20]
                    Task3[Backend Task 3<br/>10.0.11.10]
                end

                subgraph "ADK Service"
                    ADKTask1[ADK Task 1<br/>10.0.10.30]
                    ADKTask2[ADK Task 2<br/>10.0.11.20]
                end
            end
        end

        subgraph "IAM"
            ExecRole[Execution Role<br/>タスク起動権限]
            TaskRole[Task Role<br/>Supabase接続権限]
        end

        subgraph "Secrets Manager"
            Secrets[Secrets<br/>GEMINI_API_KEY<br/>SUPABASE_KEY]
        end

        subgraph "CloudWatch"
            Logs[Logs<br/>/ecs/hera-backend]
            Alarms[Alarms<br/>CPU/Memory監視]
        end
    end

    subgraph "External Services"
        Supabase[(Supabase<br/>PostgreSQL + Storage)]
        Gemini[Gemini API<br/>Google AI]
    end

    TF -.->|terraform apply| ALB
    TF -.->|terraform apply| Task1
    TF -.->|terraform apply| Task2
    TF -.->|terraform apply| Task3
    TF -.->|terraform apply| ADKTask1
    TF -.->|terraform apply| ADKTask2

    Internet((Internet)) --> IGW
    IGW --> ALB
    ALB --> Task1
    ALB --> Task2
    ALB --> Task3

    PubSub1 --> NAT1
    PubSub2 --> NAT2
    NAT1 --> PrivSub1
    NAT2 --> PrivSub2

    Task1 --> Supabase
    Task2 --> Supabase
    Task3 --> Supabase
    ADKTask1 --> Supabase
    ADKTask2 --> Supabase

    Task1 --> Gemini
    Task2 --> Gemini
    Task3 --> Gemini

    Task1 -.-> Secrets
    Task2 -.-> Secrets
    Task1 -.-> Logs
    Task2 -.-> Logs
    Logs --> Alarms

    ExecRole -.-> Task1
    TaskRole -.-> Task1

    style ALB fill:#ff9900
    style Task1 fill:#ff9900
    style Task2 fill:#ff9900
    style Task3 fill:#ff9900
    style Supabase fill:#3ecf8e
```

---

## 5. Supabase管理フロー

```mermaid
sequenceDiagram
    participant TF as Terraform
    participant SupaAPI as Supabase API
    participant SupaDB as PostgreSQL
    participant Storage as Supabase Storage
    participant RLS as Row Level Security

    Note over TF,RLS: Supabaseリソース作成

    TF->>SupaAPI: 1. プロジェクト作成
    SupaAPI-->>TF: Project ID, API URL

    TF->>SupaDB: 2. テーブル作成<br/>(schema.sql実行)
    SupaDB-->>TF: テーブル作成完了

    TF->>SupaDB: 3. インデックス作成
    SupaDB-->>TF: インデックス作成完了

    TF->>RLS: 4. RLSポリシー適用<br/>(rls_policies.sql実行)
    RLS-->>TF: ポリシー適用完了

    TF->>Storage: 5. Storageバケット作成<br/>(session-images)
    Storage-->>TF: バケット作成完了

    TF->>Storage: 6. バケットポリシー設定<br/>(Public Read)
    Storage-->>TF: ポリシー設定完了

    Note over TF,RLS: 設定完了

    TF->>TF: outputs.tf から<br/>API URL/Keyを出力
```

---

## 6. CI/CDパイプライン

```mermaid
graph TB
    subgraph "GitHub"
        PR[Pull Request<br/>terraform/変更]
        Main[Main Branch<br/>マージ後]
    end

    subgraph "GitHub Actions"
        subgraph "Plan Stage"
            Checkout1[Checkout Code]
            TFInit1[terraform init]
            TFPlan[terraform plan]
            Comment[PRにプラン結果<br/>コメント]
        end

        subgraph "Apply Stage"
            Checkout2[Checkout Code]
            TFInit2[terraform init]
            Approve{手動承認<br/>必要？}
            TFApply[terraform apply]
            Notify[Slack通知]
        end
    end

    subgraph "Terraform Backend"
        S3[(S3<br/>terraform.tfstate)]
        Lock[(DynamoDB<br/>State Lock)]
    end

    subgraph "インフラ"
        Resources[クラウドリソース<br/>作成/更新/削除]
    end

    PR --> Checkout1
    Checkout1 --> TFInit1
    TFInit1 --> S3
    TFInit1 --> Lock
    TFInit1 --> TFPlan
    TFPlan --> Comment
    Comment --> PR

    Main --> Checkout2
    Checkout2 --> TFInit2
    TFInit2 --> S3
    TFInit2 --> Lock
    TFInit2 --> Approve

    Approve -->|Dev環境| TFApply
    Approve -->|Prod環境| Manual[手動承認待ち]
    Manual --> TFApply

    TFApply --> Resources
    TFApply --> Notify

    style TFPlan fill:#4a90e2
    style TFApply fill:#27ae60
    style Manual fill:#e74c3c
    style Approve fill:#f39c12
```

---

## 7. 状態管理

```mermaid
graph TB
    subgraph "開発者環境"
        Dev1[開発者 A<br/>terraform plan]
        Dev2[開発者 B<br/>terraform plan]
    end

    subgraph "S3 Backend"
        S3State[(S3 Bucket<br/>hera-terraform-state/<br/>terraform.tfstate)]
    end

    subgraph "DynamoDB Lock"
        LockTable[(DynamoDB Table<br/>terraform-state-lock)]
    end

    subgraph "実際のインフラ"
        RealInfra[AWS/Supabase<br/>実リソース]
    end

    Dev1 -->|1. ロック取得| LockTable
    LockTable -->|2. ロック成功| Dev1
    Dev1 -->|3. 状態読み込み| S3State
    S3State -->|4. 現在の状態| Dev1
    Dev1 -->|5. 実リソース確認| RealInfra
    RealInfra -->|6. 現在の構成| Dev1
    Dev1 -->|7. 差分計算| Dev1
    Dev1 -->|8. 変更適用| RealInfra
    Dev1 -->|9. 状態更新| S3State
    Dev1 -->|10. ロック解放| LockTable

    Dev2 -->|1. ロック取得試行| LockTable
    LockTable -->|2. ロック失敗<br/>（Dev1が保持中）| Dev2
    Dev2 -.->|待機| Dev2

    style LockTable fill:#e74c3c
    style S3State fill:#3498db
    style Dev1 fill:#27ae60
    style Dev2 fill:#95a5a6
```

---

## 8. 開発フロー

```mermaid
sequenceDiagram
    participant Dev as 開発者
    participant Local as ローカル環境
    participant Git as GitHub
    participant CI as CI/CD
    participant DevInfra as Dev環境
    participant ProdInfra as Prod環境

    Note over Dev,ProdInfra: ローカルでの開発・テスト

    Dev->>Local: terraform init
    Dev->>Local: terraform plan
    Local-->>Dev: 変更内容を確認

    Dev->>Local: terraform apply
    Local->>DevInfra: リソース作成（ローカルから）
    DevInfra-->>Dev: 動作確認

    Note over Dev,ProdInfra: コードをGitにプッシュ

    Dev->>Git: git push origin feature/add-monitoring
    Git->>CI: Pull Request作成

    Note over Dev,ProdInfra: CI/CDでプランを自動実行

    CI->>CI: terraform plan (dev)
    CI->>Git: プラン結果をPRにコメント
    Dev->>Git: コードレビュー
    Dev->>Git: PR承認・マージ

    Note over Dev,ProdInfra: Dev環境へ自動デプロイ

    Git->>CI: mainブランチへマージ
    CI->>CI: terraform apply (dev)
    CI->>DevInfra: リソース更新
    DevInfra-->>Dev: 動作確認

    Note over Dev,ProdInfra: Prod環境へ手動デプロイ

    Dev->>Git: Pull Request (prod環境)
    Git->>CI: terraform plan (prod)
    CI->>Git: プラン結果をPRにコメント
    Dev->>Dev: 慎重にレビュー
    Dev->>Git: PR承認・マージ
    Git->>CI: GitHub Actions トリガー
    CI->>CI: 手動承認待ち
    Dev->>CI: 手動承認
    CI->>CI: terraform apply (prod)
    CI->>ProdInfra: リソース更新
    ProdInfra-->>Dev: 本番デプロイ完了
    CI->>Dev: Slack通知
```

---

## 9. 環境間の差異

```mermaid
graph TB
    subgraph "Development 環境"
        subgraph "Dev Config"
            DevVars[terraform.tfvars<br/>---<br/>desired_count = 1<br/>cpu = 256<br/>memory = 512<br/>plan = free]
        end

        subgraph "Dev Resources"
            DevVPC[VPC: 10.0.0.0/16<br/>2 AZs]
            DevECS[ECS: 1台<br/>0.25 vCPU<br/>512 MB RAM]
            DevSupa[Supabase: Free<br/>500MB DB]
        end

        DevVars --> DevVPC
        DevVars --> DevECS
        DevVars --> DevSupa
    end

    subgraph "Staging 環境"
        subgraph "Staging Config"
            StagingVars[terraform.tfvars<br/>---<br/>desired_count = 2<br/>cpu = 512<br/>memory = 1024<br/>plan = pro]
        end

        subgraph "Staging Resources"
            StagingVPC[VPC: 10.1.0.0/16<br/>2 AZs]
            StagingECS[ECS: 2台<br/>0.5 vCPU<br/>1 GB RAM]
            StagingSupa[Supabase: Pro<br/>8GB DB]
        end

        StagingVars --> StagingVPC
        StagingVars --> StagingECS
        StagingVars --> StagingSupa
    end

    subgraph "Production 環境"
        subgraph "Prod Config"
            ProdVars[terraform.tfvars<br/>---<br/>desired_count = 3<br/>cpu = 1024<br/>memory = 2048<br/>plan = pro<br/>multi_az = true]
        end

        subgraph "Prod Resources"
            ProdVPC[VPC: 10.2.0.0/16<br/>3 AZs<br/>High Availability]
            ProdECS[ECS: 3台<br/>1 vCPU<br/>2 GB RAM<br/>Auto Scaling]
            ProdSupa[Supabase: Pro<br/>8GB DB<br/>Auto Backup]
        end

        ProdVars --> ProdVPC
        ProdVars --> ProdECS
        ProdVars --> ProdSupa
    end

    style DevECS fill:#95a5a6
    style StagingECS fill:#3498db
    style ProdECS fill:#27ae60
    style DevSupa fill:#95a5a6
    style StagingSupa fill:#3498db
    style ProdSupa fill:#27ae60
```

---

## 10. コスト最適化フロー

```mermaid
graph TB
    subgraph "コスト監視"
        CostExplorer[AWS Cost Explorer<br/>日次コスト確認]
        SupaCost[Supabase Dashboard<br/>使用量確認]
    end

    subgraph "Terraform最適化"
        TFVars[terraform.tfvars<br/>リソース設定]
        Review{コスト<br/>問題あり？}
    end

    subgraph "最適化アクション"
        subgraph "スケールダウン"
            ReduceCount[desired_count減少<br/>3台 → 2台]
            ReduceSize[インスタンスサイズ縮小<br/>1024 → 512 CPU]
        end

        subgraph "不要リソース削除"
            RemoveNAT[NAT Gateway削減<br/>2台 → 1台]
            RemoveEnv[Dev環境削除<br/>夜間・週末]
        end

        subgraph "予約購入"
            Reserved[Reserved Capacity<br/>長期契約で割引]
        end
    end

    subgraph "実行"
        TFPlan[terraform plan]
        TFApply[terraform apply]
        Monitor[コスト再確認]
    end

    CostExplorer --> Review
    SupaCost --> Review

    Review -->|YES| ReduceCount
    Review -->|YES| ReduceSize
    Review -->|YES| RemoveNAT
    Review -->|YES| RemoveEnv
    Review -->|NO| Monitor

    ReduceCount --> TFVars
    ReduceSize --> TFVars
    RemoveNAT --> TFVars
    RemoveEnv --> TFVars

    TFVars --> TFPlan
    TFPlan --> TFApply
    TFApply --> Monitor
    Monitor --> CostExplorer

    Reserved -.->|別途手動| Monitor

    style Review fill:#f39c12
    style ReduceCount fill:#27ae60
    style ReduceSize fill:#27ae60
    style RemoveNAT fill:#e74c3c
    style Monitor fill:#3498db
```

---

## 11. Terraformのメリット可視化

```mermaid
graph LR
    subgraph "手動管理の課題"
        Manual1[手動作業<br/>時間がかかる]
        Manual2[ミス発生<br/>設定漏れ]
        Manual3[ドキュメント<br/>陳腐化]
        Manual4[環境差異<br/>再現困難]
    end

    subgraph "Terraformの解決策"
        TF1[コード化<br/>自動化]
        TF2[冪等性<br/>ミス防止]
        TF3[コードが<br/>ドキュメント]
        TF4[完全な<br/>再現性]
    end

    subgraph "得られるメリット"
        Benefit1[開発速度<br/>4倍向上]
        Benefit2[ミス<br/>90%削減]
        Benefit3[ドキュメント<br/>常に最新]
        Benefit4[環境構築<br/>10分で完了]
    end

    Manual1 -.->|解決| TF1
    Manual2 -.->|解決| TF2
    Manual3 -.->|解決| TF3
    Manual4 -.->|解決| TF4

    TF1 --> Benefit1
    TF2 --> Benefit2
    TF3 --> Benefit3
    TF4 --> Benefit4

    style Manual1 fill:#e74c3c
    style Manual2 fill:#e74c3c
    style Manual3 fill:#e74c3c
    style Manual4 fill:#e74c3c
    style TF1 fill:#3498db
    style TF2 fill:#3498db
    style TF3 fill:#3498db
    style TF4 fill:#3498db
    style Benefit1 fill:#27ae60
    style Benefit2 fill:#27ae60
    style Benefit3 fill:#27ae60
    style Benefit4 fill:#27ae60
```

---

## 12. リソース依存関係グラフ

```mermaid
graph TB
    VPC[VPC]
    IGW[Internet Gateway]
    PubSub[Public Subnets]
    PrivSub[Private Subnets]
    NAT[NAT Gateways]
    SG[Security Groups]
    ALB[Application LB]
    ECSCluster[ECS Cluster]
    TaskDef[Task Definition]
    ECSService[ECS Service]
    IAMExec[IAM Execution Role]
    IAMTask[IAM Task Role]
    Secrets[Secrets Manager]
    LogGroup[CloudWatch Logs]
    SupaProject[Supabase Project]
    SupaDB[Supabase Database]
    SupaStorage[Supabase Storage]

    VPC --> PubSub
    VPC --> PrivSub
    VPC --> IGW
    VPC --> SG
    PubSub --> NAT
    PubSub --> ALB
    NAT --> PrivSub
    SG --> ALB
    SG --> ECSService

    ECSCluster --> ECSService
    TaskDef --> ECSService
    IAMExec --> TaskDef
    IAMTask --> TaskDef
    Secrets --> TaskDef
    LogGroup --> TaskDef
    PrivSub --> ECSService
    ALB --> ECSService

    SupaProject --> SupaDB
    SupaProject --> SupaStorage

    SupaDB -.->|接続| ECSService
    SupaStorage -.->|接続| ECSService

    style VPC fill:#ff9900
    style ECSService fill:#ff9900
    style SupaDB fill:#3ecf8e
    style SupaStorage fill:#3ecf8e
```

**Terraformが自動的に依存関係を解決し、正しい順序でリソースを作成します！**

---

## まとめ

### Terraformのメリット

1. **インフラのコード化**: 全ての設定がコードで管理される
2. **バージョン管理**: Gitで変更履歴を追跡
3. **環境の再現性**: 同じコードから同じ環境を再現
4. **変更の可視化**: `terraform plan` で事前確認
5. **チーム協業**: 状態管理とロック機構で安全に協業
6. **マルチクラウド**: AWS + Supabase を統一的に管理

### 推奨される使用ケース

- ✅ 複数環境の管理（dev/staging/prod）
- ✅ チーム開発
- ✅ 長期運用プロジェクト
- ✅ インフラの頻繁な変更
- ✅ コンプライアンス要件（監査証跡）

### 初期投資

- **セットアップ時間**: 18-26時間
- **学習コスト**: HCLの基本（2-3日）
- **運用コスト**: Terraform Cloud $20/月（オプション）

### 長期的なROI

- **開発速度**: 4倍向上
- **ミス削減**: 90%削減
- **運用工数**: 月10時間 → 月2時間

**Terraformは初期投資が必要ですが、長期的には大幅なコスト削減と品質向上を実現します。**
