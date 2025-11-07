# Terraform統合計画

**作成日**: 2025-10-28
**対象**: HeraプロジェクトのインフラをTerraformでコード化

---

## 📋 目次

1. [Terraformとは](#terraformとは)
2. [適用するリソース](#適用するリソース)
3. [ディレクトリ構成](#ディレクトリ構成)
4. [実装例](#実装例)
5. [環境別管理](#環境別管理)
6. [デプロイフロー](#デプロイフロー)
7. [メリット・デメリット](#メリットデメリット)

---

## 1. Terraformとは

### Infrastructure as Code (IaC)

Terraformは、インフラをコードで定義・管理するツールです。

```hcl
# コードでインフラを定義
resource "aws_ecs_service" "backend" {
  name            = "hera-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 2
}
```

### 主な特徴

✅ **宣言的な記述**: 「どうするか」ではなく「何を作るか」を記述
✅ **冪等性**: 何度実行しても同じ結果
✅ **状態管理**: 現在のインフラ状態を追跡
✅ **依存関係解決**: リソース間の依存関係を自動管理
✅ **マルチクラウド**: AWS、GCP、Azure、Supabaseなど統一的に管理

---

## 2. 適用するリソース

### 2.1 Supabaseリソース

```
- データベーススキーマ（テーブル、インデックス）
- Storage バケット
- Row Level Security (RLS) ポリシー
- データベース関数・トリガー
- API設定
```

### 2.2 クラウドインフラ（AWS例）

```
- ECS クラスター
- ECS タスク定義（Backend、Frontend、ADK）
- Application Load Balancer (ALB)
- VPC、サブネット、セキュリティグループ
- IAM ロール・ポリシー
- CloudWatch ログ
- Route53 DNS設定
- ACM 証明書
```

### 2.3 その他

```
- 環境変数（AWS Systems Manager Parameter Store）
- シークレット管理（AWS Secrets Manager）
- モニタリング（CloudWatch Alarms）
```

---

## 3. ディレクトリ構成

```
hera/
├── terraform/
│   ├── modules/                    # 再利用可能なモジュール
│   │   ├── supabase/              # Supabase構成
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── ecs/                   # ECS構成
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   └── networking/            # VPC・ネットワーク
│   │       ├── main.tf
│   │       ├── variables.tf
│   │       └── outputs.tf
│   │
│   ├── environments/              # 環境別設定
│   │   ├── dev/
│   │   │   ├── main.tf
│   │   │   ├── terraform.tfvars
│   │   │   └── backend.tf
│   │   ├── staging/
│   │   │   ├── main.tf
│   │   │   ├── terraform.tfvars
│   │   │   └── backend.tf
│   │   └── prod/
│   │       ├── main.tf
│   │       ├── terraform.tfvars
│   │       └── backend.tf
│   │
│   ├── providers.tf               # プロバイダー設定
│   ├── variables.tf               # 共通変数
│   └── outputs.tf                 # 出力値
│
├── backend/
├── frontend/
└── adk/
```

---

## 4. 実装例

### 4.1 プロバイダー設定

**terraform/providers.tf**

```hcl
terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    supabase = {
      source  = "supabase/supabase"
      version = "~> 1.0"
    }
  }

  # 状態管理をS3バックエンドで
  backend "s3" {
    bucket         = "hera-terraform-state"
    key            = "terraform.tfstate"
    region         = "ap-northeast-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region = var.aws_region
}

provider "supabase" {
  access_token = var.supabase_access_token
  project_id   = var.supabase_project_id
}
```

### 4.2 Supabaseモジュール

**terraform/modules/supabase/main.tf**

```hcl
# Supabaseプロジェクト
resource "supabase_project" "main" {
  name           = var.project_name
  organization_id = var.organization_id
  database_password = var.database_password
  region         = var.region
  plan           = var.plan  # "free" or "pro"
}

# Storage バケット
resource "supabase_storage_bucket" "session_images" {
  name     = "session-images"
  public   = true
  project_id = supabase_project.main.id

  file_size_limit = 5242880  # 5MB
  allowed_mime_types = [
    "image/png",
    "image/jpeg",
    "image/webp"
  ]
}

# データベーススキーマ
resource "supabase_sql" "schema" {
  project_id = supabase_project.main.id

  query = file("${path.module}/schema.sql")
}

# RLSポリシー
resource "supabase_sql" "rls_policies" {
  project_id = supabase_project.main.id
  depends_on = [supabase_sql.schema]

  query = file("${path.module}/rls_policies.sql")
}
```

**terraform/modules/supabase/schema.sql**

```sql
-- sessions テーブル
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'active'
);

CREATE INDEX idx_sessions_session_id ON sessions(session_id);
CREATE INDEX idx_sessions_created_at ON sessions(created_at);

-- user_profiles テーブル
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    name TEXT,
    age INTEGER,
    partner_name TEXT,
    hobbies JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(session_id)
);

-- 以下、他のテーブル定義...
```

**terraform/modules/supabase/rls_policies.sql**

```sql
-- RLSを有効化
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_history ENABLE ROW LEVEL SECURITY;

-- ポリシー: 全員が自分のセッションを読み取り可能
CREATE POLICY "Users can read own sessions"
ON sessions FOR SELECT
USING (true);

CREATE POLICY "Users can insert own sessions"
ON sessions FOR INSERT
WITH CHECK (true);

-- ユーザープロファイルのポリシー
CREATE POLICY "Users can read own profiles"
ON user_profiles FOR SELECT
USING (true);

CREATE POLICY "Users can update own profiles"
ON user_profiles FOR UPDATE
USING (true);
```

### 4.3 ECSモジュール

**terraform/modules/ecs/main.tf**

```hcl
# ECS クラスター
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# Backend タスク定義
resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.project_name}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.backend_cpu
  memory                   = var.backend_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "backend"
      image = "${var.ecr_repository_url}:backend-${var.image_tag}"

      portMappings = [
        {
          containerPort = 8080
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "SUPABASE_URL"
          value = var.supabase_url
        },
        {
          name  = "STORAGE_MODE"
          value = "supabase"
        }
      ]

      secrets = [
        {
          name      = "GEMINI_API_KEY"
          valueFrom = aws_secretsmanager_secret.gemini_api_key.arn
        },
        {
          name      = "SUPABASE_KEY"
          valueFrom = aws_secretsmanager_secret.supabase_key.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.backend.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "backend"
        }
      }
    }
  ])
}

# Backend サービス
resource "aws_ecs_service" "backend" {
  name            = "${var.project_name}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.backend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.backend.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8080
  }

  depends_on = [aws_lb_listener.backend]
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = var.environment == "prod" ? true : false
}

# Target Group
resource "aws_lb_target_group" "backend" {
  name        = "${var.project_name}-backend"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 10
    timeout             = 60
    interval            = 300
    matcher             = "200"
  }
}

# Listener
resource "aws_lb_listener" "backend" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.main.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}
```

### 4.4 ネットワークモジュール

**terraform/modules/networking/main.tf**

```hcl
# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = var.availability_zones[count.index]

  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-${count.index + 1}"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "${var.project_name}-private-${count.index + 1}"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# NAT Gateway
resource "aws_eip" "nat" {
  count  = length(var.availability_zones)
  domain = "vpc"
}

resource "aws_nat_gateway" "main" {
  count         = length(var.availability_zones)
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name = "${var.project_name}-nat-${count.index + 1}"
  }
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-public"
  }
}

resource "aws_route_table" "private" {
  count  = length(var.availability_zones)
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = {
    Name = "${var.project_name}-private-${count.index + 1}"
  }
}
```

---

## 5. 環境別管理

### 5.1 開発環境

**terraform/environments/dev/main.tf**

```hcl
module "networking" {
  source = "../../modules/networking"

  project_name       = "hera-dev"
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["ap-northeast-1a", "ap-northeast-1c"]
  environment        = "dev"
}

module "supabase" {
  source = "../../modules/supabase"

  project_name      = "hera-dev"
  organization_id   = var.supabase_org_id
  database_password = var.supabase_db_password
  region            = "ap-northeast-1"
  plan              = "free"
}

module "ecs" {
  source = "../../modules/ecs"

  project_name           = "hera-dev"
  environment            = "dev"
  vpc_id                 = module.networking.vpc_id
  public_subnet_ids      = module.networking.public_subnet_ids
  private_subnet_ids     = module.networking.private_subnet_ids

  backend_desired_count  = 1  # 開発環境は1台
  backend_cpu            = "256"
  backend_memory         = "512"

  supabase_url           = module.supabase.api_url
  ecr_repository_url     = var.ecr_repository_url
  image_tag              = "latest"
}
```

**terraform/environments/dev/terraform.tfvars**

```hcl
aws_region          = "ap-northeast-1"
supabase_org_id     = "your-org-id"
ecr_repository_url  = "123456789012.dkr.ecr.ap-northeast-1.amazonaws.com/hera"
```

### 5.2 本番環境

**terraform/environments/prod/main.tf**

```hcl
module "networking" {
  source = "../../modules/networking"

  project_name       = "hera-prod"
  vpc_cidr           = "10.1.0.0/16"
  availability_zones = ["ap-northeast-1a", "ap-northeast-1c", "ap-northeast-1d"]
  environment        = "prod"
}

module "supabase" {
  source = "../../modules/supabase"

  project_name      = "hera-prod"
  organization_id   = var.supabase_org_id
  database_password = var.supabase_db_password
  region            = "ap-northeast-1"
  plan              = "pro"  # 本番はProプラン
}

module "ecs" {
  source = "../../modules/ecs"

  project_name           = "hera-prod"
  environment            = "prod"
  vpc_id                 = module.networking.vpc_id
  public_subnet_ids      = module.networking.public_subnet_ids
  private_subnet_ids     = module.networking.private_subnet_ids

  backend_desired_count  = 3  # 本番は3台（High Availability）
  backend_cpu            = "1024"
  backend_memory         = "2048"

  supabase_url           = module.supabase.api_url
  ecr_repository_url     = var.ecr_repository_url
  image_tag              = var.image_tag  # 本番はタグ指定
}
```

---

## 6. デプロイフロー

### 6.1 初回セットアップ

```bash
# Terraformのインストール
brew install terraform  # macOS
# または
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip

# プロジェクトディレクトリに移動
cd hera/terraform/environments/dev

# 初期化
terraform init

# プラン確認
terraform plan

# 適用
terraform apply
```

### 6.2 CI/CDパイプライン

**GitHub Actions例 (.github/workflows/terraform.yml)**

```yaml
name: Terraform

on:
  push:
    branches:
      - main
    paths:
      - 'terraform/**'
  pull_request:
    paths:
      - 'terraform/**'

jobs:
  terraform:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.6.0

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-1

      - name: Terraform Init
        working-directory: terraform/environments/dev
        run: terraform init

      - name: Terraform Plan
        working-directory: terraform/environments/dev
        run: terraform plan -out=tfplan

      - name: Terraform Apply
        if: github.ref == 'refs/heads/main'
        working-directory: terraform/environments/dev
        run: terraform apply -auto-approve tfplan
```

### 6.3 通常の運用

```bash
# 開発環境の更新
cd terraform/environments/dev
terraform plan
terraform apply

# 本番環境の更新（承認プロセス付き）
cd terraform/environments/prod
terraform plan -out=prod.tfplan
# レビュー後
terraform apply prod.tfplan

# 特定のリソースのみ更新
terraform apply -target=module.ecs.aws_ecs_service.backend

# リソースの削除（環境全体）
terraform destroy  # 注意: 本番では使用禁止
```

---

## 7. メリット・デメリット

### メリット ✅

#### 1. **コードによる管理**
```hcl
# インフラの設定が明確
resource "aws_ecs_service" "backend" {
  desired_count = 3  # 台数を変更したい場合はここを変更
}
```

#### 2. **バージョン管理**
```bash
$ git log terraform/
commit abc123 Update backend task count to 3
commit def456 Add staging environment
commit ghi789 Initial Terraform setup
```

#### 3. **変更の可視化**
```bash
$ terraform plan
  ~ update in-place
  - destroy
  + create

Plan: 1 to add, 2 to change, 0 to destroy.
```

#### 4. **環境の再現**
```bash
# 開発環境を10秒で再構築
terraform destroy -auto-approve
terraform apply -auto-approve
```

#### 5. **ドリフト検出**
```bash
# コンソールで手動変更した場合に検出
$ terraform plan
Note: Objects have changed outside of Terraform
```

#### 6. **ドキュメント化**
- コードそのものがドキュメント
- 構成が明確
- レビューが容易

### デメリット ⚠️

#### 1. **学習コスト**
- HCL（HashiCorp Configuration Language）の学習が必要
- 各プロバイダーのリソース定義を理解する必要

#### 2. **初期セットアップの手間**
- モジュール設計
- 状態管理の設定
- CI/CD統合

#### 3. **状態管理の複雑さ**
- terraform.tfstate の管理
- ロック機構が必要（DynamoDB）
- チーム協業時の競合

#### 4. **全てがコード化できるわけではない**
- 一部の手動操作が必要な場合がある
- プロバイダーが対応していないリソースもある

---

## 8. コスト比較

### 手動管理（現状）

| 項目 | コスト |
|------|--------|
| 人件費（環境構築） | 8時間 × 人件費 |
| 人件費（運用・変更） | 2時間/月 × 人件費 |
| **ミスのリスク** | 高い |

### Terraform管理

| 項目 | コスト |
|------|--------|
| 初期セットアップ | 16時間 × 人件費（初回のみ） |
| 人件費（運用・変更） | 0.5時間/月 × 人件費 |
| Terraform Cloud（オプション） | $20/月（チーム協業） |
| **ミスのリスク** | 低い |

**結論**: 初期投資は必要だが、長期的には大幅にコスト削減

---

## 9. 推奨構成

### Option A: Terraform + Supabase + AWS ECS（推奨）

```
✅ 完全なInfrastructure as Code
✅ Supabase（DB + Storage）はTerraformで管理
✅ ECS（コンテナ）もTerraformで管理
✅ 環境の完全な再現性
✅ CI/CDとの統合
```

**推定セットアップ時間**: 16-20時間
**月額コスト**: Supabase Pro $25 + AWS ECS $50 = **$75/月**

### Option B: Terraform + Supabase のみ

```
✅ SupabaseリソースのみTerraformで管理
✅ コンテナは手動デプロイ（Vercel、Cloud Runなど）
✅ 軽量なセットアップ
```

**推定セットアップ時間**: 6-8時間
**月額コスト**: Supabase Pro $25 + Vercel $0 = **$25/月**

### Option C: 手動管理（現状維持）

```
⚠️ GUIでの手動設定
⚠️ ドキュメント化が必要
⚠️ 環境の再現が困難
```

**推定セットアップ時間**: 4-6時間（初回のみ）
**月額コスト**: Supabase Pro $25 = **$25/月**

---

## 10. 実装タスクリスト

### Phase 1: Terraform基盤構築（4-6時間）
- [ ] Terraformディレクトリ構成作成
- [ ] プロバイダー設定
- [ ] S3バックエンド設定（状態管理）
- [ ] DynamoDB テーブル作成（ロック管理）
- [ ] 基本モジュール作成

### Phase 2: Supabaseモジュール（3-4時間）
- [ ] Supabaseプロバイダー設定
- [ ] データベーススキーマのTerraform化
- [ ] Storage バケットのTerraform化
- [ ] RLSポリシーのTerraform化
- [ ] テスト実行

### Phase 3: AWSモジュール（6-8時間）
- [ ] ネットワークモジュール（VPC、Subnet）
- [ ] ECSモジュール（Cluster、Task、Service）
- [ ] ALBモジュール（Load Balancer）
- [ ] IAMロール・ポリシー
- [ ] CloudWatch ログ設定

### Phase 4: 環境別設定（2-3時間）
- [ ] dev環境設定
- [ ] staging環境設定
- [ ] prod環境設定
- [ ] 環境変数管理（tfvars）

### Phase 5: CI/CD統合（2-3時間）
- [ ] GitHub Actions ワークフロー作成
- [ ] terraform plan の自動実行
- [ ] terraform apply の承認フロー
- [ ] Slack通知統合

### Phase 6: ドキュメント（1-2時間）
- [ ] Terraform運用ガイド作成
- [ ] トラブルシューティングガイド
- [ ] チーム向けのREADME

**推定合計時間**: 18-26時間

---

## 11. 結論

### Terraformを使うべき場合 ✅

- ✅ 複数環境を管理する（dev/staging/prod）
- ✅ チームで開発している
- ✅ インフラの変更が頻繁にある
- ✅ 環境の再現性を重視
- ✅ 長期運用を見据えている

### 手動管理を続けるべき場合 ⚠️

- ⚠️ 単一環境のみ（prodのみ）
- ⚠️ 個人プロジェクト
- ⚠️ インフラがほとんど変わらない
- ⚠️ 初期投資の時間がない
- ⚠️ Terraformの学習時間が取れない

---

## 12. 次のステップ

### 推奨アプローチ

**段階的な導入を推奨**:

1. **Phase 1**: Supabaseリソースのみ Terraform化（6-8時間）
   - データベーススキーマ
   - Storage バケット
   - RLSポリシー

2. **Phase 2**: AWS ECSをTerraform化（10-12時間）
   - VPC・ネットワーク
   - ECS構成
   - ALB

3. **Phase 3**: CI/CD統合（2-3時間）
   - GitHub Actions
   - 自動デプロイ

**合計**: 18-23時間で完全なInfrastructure as Codeが完成

---

## 13. 実装開始判断

### A: Terraform導入を推奨

以下の条件に1つでも当てはまる場合:
- [ ] 複数環境（dev/staging/prod）を運用する
- [ ] チームメンバーが2人以上
- [ ] インフラの変更が月1回以上ある
- [ ] 長期運用予定（6ヶ月以上）

### B: 現状維持を推奨

以下の条件に全て当てはまる場合:
- [ ] 単一環境のみ
- [ ] 個人プロジェクト
- [ ] インフラがほぼ固定
- [ ] 短期プロジェクト（3ヶ月以内）

---

**Terraform導入を開始しますか？**
