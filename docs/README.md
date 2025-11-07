# ドキュメント

このディレクトリには、Heraプロジェクトの各種ドキュメントが格納されています。

## 📁 ディレクトリ構造

```
docs/
├── deployment/     # デプロイメント関連ドキュメント
├── architecture/   # アーキテクチャ・設計ドキュメント
├── migration/      # 移行関連ドキュメント
└── reports/        # レポート・分析ドキュメント
```

## 📋 ドキュメント一覧

### デプロイメント (`deployment/`)

- **[DEPLOYMENT.md](deployment/DEPLOYMENT.md)** - 最新のデプロイメントガイド（Docker、Cloud Run対応）
- **[DEPLOYMENT_GUIDE.md](deployment/DEPLOYMENT_GUIDE.md)** - 旧デプロイメントガイド
- **[DOCKER.md](deployment/DOCKER.md)** - Docker構成の詳細
- **[GCP_CLOUD_RUN_DEPLOYMENT_PLAN.md](deployment/GCP_CLOUD_RUN_DEPLOYMENT_PLAN.md)** - Cloud Runデプロイ計画
- **[VERCEL_DEPLOYMENT_PLAN.md](deployment/VERCEL_DEPLOYMENT_PLAN.md)** - Vercelデプロイ計画（非推奨）

### アーキテクチャ・設計 (`architecture/`)

- **[MASTER_INTEGRATION_PLAN.md](architecture/MASTER_INTEGRATION_PLAN.md)** - 統合マスタープラン
- **[MASTER_PLAN_VERCEL.md](architecture/MASTER_PLAN_VERCEL.md)** - Vercel版マスタープラン
- **[SYSTEM_FLOW_DIAGRAMS.md](architecture/SYSTEM_FLOW_DIAGRAMS.md)** - システムフロー図
- **[SUPABASE_ARCHITECTURE_DIAGRAMS.md](architecture/SUPABASE_ARCHITECTURE_DIAGRAMS.md)** - Supabaseアーキテクチャ図（旧）
- **[SUPABASE_AUTH_DIAGRAMS.md](architecture/SUPABASE_AUTH_DIAGRAMS.md)** - Supabase認証図（旧）
- **[SUPABASE_AUTH_INTEGRATION_PLAN.md](architecture/SUPABASE_AUTH_INTEGRATION_PLAN.md)** - Supabase認証統合計画（旧）
- **[SUPABASE_INTEGRATION_PLAN.md](architecture/SUPABASE_INTEGRATION_PLAN.md)** - Supabase統合計画（旧）
- **[TERRAFORM_ARCHITECTURE_DIAGRAMS.md](architecture/TERRAFORM_ARCHITECTURE_DIAGRAMS.md)** - Terraformアーキテクチャ図
- **[TERRAFORM_INTEGRATION_PLAN.md](architecture/TERRAFORM_INTEGRATION_PLAN.md)** - Terraform統合計画
- **[VERCEL_ARCHITECTURE_DIAGRAMS.md](architecture/VERCEL_ARCHITECTURE_DIAGRAMS.md)** - Vercelアーキテクチャ図

### 移行 (`migration/`)

- **[GCP_MIGRATION_PLAN.md](migration/GCP_MIGRATION_PLAN.md)** - SupabaseからFirebase/GCPへの移行計画
- **[REDIS_SUPABASE_MIGRATION_DIAGRAMS.md](migration/REDIS_SUPABASE_MIGRATION_DIAGRAMS.md)** - Redis-Supabase移行図

### レポート・分析 (`reports/`)

- **[CONTAINER_NETWORK_VERIFICATION.md](reports/CONTAINER_NETWORK_VERIFICATION.md)** - コンテナネットワーク検証レポート
- **[CRITICAL_IMPLEMENTATION_GAP.md](reports/CRITICAL_IMPLEMENTATION_GAP.md)** - 重大な実装ギャップの分析
- **[FIXES_APPLIED.md](reports/FIXES_APPLIED.md)** - 適用済み修正のまとめ
- **[FLOW_ANALYSIS_REPORT.md](reports/FLOW_ANALYSIS_REPORT.md)** - フロー分析レポート
- **[REDIS_INTEGRATION_SUMMARY.md](reports/REDIS_INTEGRATION_SUMMARY.md)** - Redis統合サマリー
- **[REDIS_VS_SUPABASE_COMPARISON.md](reports/REDIS_VS_SUPABASE_COMPARISON.md)** - Redis vs Supabase 比較

## 🚀 クイックスタート

プロジェクトを始めるには、まず以下のドキュメントを参照してください：

1. **[プロジェクトルートのREADME.md](../README.md)** - プロジェクトの概要
2. **[deployment/DEPLOYMENT.md](deployment/DEPLOYMENT.md)** - デプロイ手順

## 📝 現在のアーキテクチャ

**2025年1月時点:** プロジェクトはSupabaseからFirebase/GCPに完全移行済みです。

- **認証:** Firebase Authentication
- **データベース:** Cloud Firestore
- **ストレージ:** Google Cloud Storage
- **ホスティング:** Cloud Run（推奨）

旧Supabase関連のドキュメントは参考資料として保管されています。

## 📧 サポート

質問や問題がある場合は、GitHubのIssuesで報告してください。
