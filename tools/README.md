# Tools Directory

AI Family Simulator開発用の補助スクリプト集

## 📁 ディレクトリ構成

```
tools/
├── setup/           # 環境セットアップ
├── database/        # データベース管理
├── docker/          # Docker操作
├── testing/         # テスト実行
├── quality/         # コード品質
├── agents/          # ADKエージェント管理
├── deploy/          # デプロイメント
├── monitoring/      # 監視・ログ
├── utils/           # ユーティリティ
├── ci/              # CI/CD補助
└── mock-server/     # モックAPIサーバー
```

## 🚀 クイックスタート

### 初回セットアップ
```bash
# 完全なセットアップを実行
./tools/setup/setup-dev.sh

# または手動で
./tools/setup/install-deps.sh    # 依存関係インストール
./tools/setup/init-env.sh        # 環境変数初期化
```

### 開発環境の起動
```bash
# ADKエージェントを起動
./tools/agents/start-hera.sh      # Heraエージェント
./tools/agents/start-family.sh    # Familyエージェント

# モックサーバーを起動
./tools/mock-server/start-mock.sh
```

## 📋 カテゴリ別スクリプト

### 🔧 Setup（環境セットアップ）

| スクリプト | 説明 |
|-----------|------|
| `install-deps.sh` | 全依存関係の一括インストール |
| `init-env.sh` | 環境変数ファイルの初期化 |
| `setup-dev.sh` | 開発環境の完全セットアップ |

**使用例:**
```bash
./tools/setup/setup-dev.sh
```

---

### 🗄️ Database（データベース管理）

| スクリプト | 説明 |
|-----------|------|
| `db-migrate.sh` | マイグレーション実行 |
| `db-reset.sh` | データベースリセット（全データ削除） |
| `db-seed.sh` | サンプルデータ投入 |
| `db-backup.sh` | バックアップ作成 |
| `db-restore.sh` | バックアップからリストア |

**使用例:**
```bash
# マイグレーション実行
./tools/database/db-migrate.sh

# バックアップ作成
./tools/database/db-backup.sh

# リストア
./tools/database/db-restore.sh backups/database/ai_family_sim_20241023_120000.sql
```

---

### 🐳 Docker（Docker操作）

| スクリプト | 説明 |
|-----------|------|
| `docker-build-all.sh` | 全サービスのイメージビルド |
| `docker-clean.sh` | 未使用リソースのクリーンアップ |
| `docker-logs.sh` | サービスログの表示 |
| `docker-restart.sh` | サービスの再起動 |

**使用例:**
```bash
# 全イメージをビルド
./tools/docker/docker-build-all.sh

# バックエンドのログを表示
./tools/docker/docker-logs.sh backend --follow

# サービスを再起動
./tools/docker/docker-restart.sh backend
```

---

### 🧪 Testing（テスト実行）

| スクリプト | 説明 |
|-----------|------|
| `run-tests.sh` | 全テスト実行 |
| `test-coverage.sh` | カバレッジレポート生成 |
| `test-integration.sh` | 統合テスト実行 |

**使用例:**
```bash
# 全テストを実行
./tools/testing/run-tests.sh

# カバレッジレポート生成
./tools/testing/test-coverage.sh
```

---

### ✨ Quality（コード品質）

| スクリプト | 説明 |
|-----------|------|
| `format-all.sh` | コードフォーマット実行 |
| `lint-all.sh` | リンティング実行 |
| `check-all.sh` | フォーマット・リント・型チェック一括実行 |

**使用例:**
```bash
# コードを自動フォーマット
./tools/quality/format-all.sh

# リンティングチェック
./tools/quality/lint-all.sh

# 全品質チェックを実行
./tools/quality/check-all.sh
```

**推奨ワークフロー:**
1. コード編集後に `format-all.sh` で整形
2. コミット前に `check-all.sh` で品質確認

---

### 🤖 Agents（ADKエージェント管理）

| スクリプト | 説明 |
|-----------|------|
| `start-hera.sh` | Heraエージェント起動 |
| `start-family.sh` | Familyエージェント起動 |
| `check-sessions.sh` | セッションデータ確認 |
| `clean-sessions.sh` | 古いセッションデータ削除 |

**使用例:**
```bash
# Heraエージェントを起動
./tools/agents/start-hera.sh

# セッションデータを確認
./tools/agents/check-sessions.sh

# 7日以上古いセッションを削除
./tools/agents/clean-sessions.sh 7
```

---

### 🚢 Deploy（デプロイメント）

| スクリプト | 説明 |
|-----------|------|
| `deploy-staging.sh` | ステージング環境へデプロイ |
| `deploy-production.sh` | 本番環境へデプロイ |
| `health-check.sh` | ヘルスチェック実行 |

**使用例:**
```bash
# ステージングへデプロイ
./tools/deploy/deploy-staging.sh

# ヘルスチェック
./tools/deploy/health-check.sh staging
```

---

### 📊 Monitoring（監視・ログ）

| スクリプト | 説明 |
|-----------|------|
| `view-logs.sh` | サービスログの表示 |

**使用例:**
```bash
# インタラクティブにサービス選択
./tools/monitoring/view-logs.sh

# 直接指定
./tools/monitoring/view-logs.sh backend
```

---

### 🛠️ Utils（ユーティリティ）

| スクリプト | 説明 |
|-----------|------|
| `generate-secret.sh` | JWT秘密鍵の生成 |
| `check-ports.sh` | 使用中ポートの確認 |
| `cleanup-temp.sh` | 一時ファイルのクリーンアップ |
| `update-deps.sh` | 依存関係のアップデート |

**使用例:**
```bash
# JWT秘密鍵を生成
./tools/utils/generate-secret.sh

# ポートの使用状況を確認
./tools/utils/check-ports.sh

# 一時ファイルをクリーンアップ
./tools/utils/cleanup-temp.sh
```

---

### 🔄 CI（CI/CD補助）

| スクリプト | 説明 |
|-----------|------|
| `pre-commit-hook.sh` | コミット前チェック |
| `validate-pr.sh` | PRバリデーション |
| `build-and-test.sh` | ビルド＆テストパイプライン |

**使用例:**
```bash
# コミット前チェック
./tools/ci/pre-commit-hook.sh

# PR作成前のバリデーション
./tools/ci/validate-pr.sh

# CI/CDパイプライン実行
./tools/ci/build-and-test.sh
```

**Git Hookの設定:**
```bash
# pre-commitフックを設定
ln -s ../../tools/ci/pre-commit-hook.sh .git/hooks/pre-commit
```

---

### 🎭 Mock Server（モックAPIサーバー）

詳細は [mock-server/README.md](mock-server/README.md) を参照

**クイックスタート:**
```bash
# モックサーバー起動
./tools/mock-server/start-mock.sh

# 別ターミナルでテスト
curl http://localhost:3001/api/v1/health
```

**主なエンドポイント:**
- `GET /api/v1/health` - ヘルスチェック
- `POST /api/v1/simulate` - シミュレーション実行
- `POST /api/v1/stories/generate` - ストーリー生成
- `POST /api/v1/letters/generate` - 手紙生成
- `POST /api/v1/images/generate` - 画像生成

---

## 🔥 よく使うワークフロー

### 開発開始時
```bash
# 1. 環境セットアップ（初回のみ）
./tools/setup/setup-dev.sh

# 2. 依存関係をインストール
./tools/setup/install-deps.sh

# 3. Dockerサービスを起動
docker compose up -d

# 4. ADKエージェントまたはモックサーバーを起動
./tools/agents/start-hera.sh
# または
./tools/mock-server/start-mock.sh
```

### コミット前
```bash
# 1. コードをフォーマット
./tools/quality/format-all.sh

# 2. 全品質チェック
./tools/quality/check-all.sh

# 3. テスト実行
./tools/testing/run-tests.sh

# 4. コミット
git add .
git commit -m "your message"
```

### PR作成前
```bash
# PRバリデーション実行
./tools/ci/validate-pr.sh

# 問題なければPR作成
```

### デプロイ前
```bash
# 1. 全チェック
./tools/ci/build-and-test.sh

# 2. ステージングへデプロイ
./tools/deploy/deploy-staging.sh

# 3. ヘルスチェック
./tools/deploy/health-check.sh staging
```

---

## 🐛 トラブルシューティング

### ポートが使用中
```bash
# 使用中ポートを確認
./tools/utils/check-ports.sh

# ポートを解放
kill -9 <PID>
```

### データベース接続エラー
```bash
# データベースを再起動
./tools/docker/docker-restart.sh db

# または完全リセット
./tools/database/db-reset.sh
```

### 依存関係エラー
```bash
# 一時ファイルをクリーンアップ
./tools/utils/cleanup-temp.sh

# 依存関係を再インストール
./tools/setup/install-deps.sh
```

### セッションデータの確認
```bash
# セッションデータを確認
./tools/agents/check-sessions.sh

# 古いセッションを削除
./tools/agents/clean-sessions.sh 7
```

---

## 💡 Tips

### スクリプトを短縮コマンド化
bashrcやzshrcに以下を追加:

```bash
# AI Family Simulator Tools
alias afs-setup='./tools/setup/setup-dev.sh'
alias afs-test='./tools/testing/run-tests.sh'
alias afs-format='./tools/quality/format-all.sh'
alias afs-check='./tools/quality/check-all.sh'
alias afs-hera='./tools/agents/start-hera.sh'
alias afs-family='./tools/agents/start-family.sh'
alias afs-mock='./tools/mock-server/start-mock.sh'
```

### 全スクリプトを実行可能にする
```bash
find tools -name "*.sh" -exec chmod +x {} \;
```

---

## 📚 参考資料

- [開発ガイド](../docs/DEVELOPMENT.md)
- [デプロイメント設計](../docs/DEPLOYMENT.md)
- [API仕様](../docs/API_SPEC.md)
- [データベーススキーマ](../docs/DATABASE_SCHEMA.md)

---

## 🤝 貢献

新しいスクリプトを追加する場合:

1. 適切なカテゴリディレクトリに配置
2. 実行権限を付与（`chmod +x`）
3. このREADMEを更新
4. スクリプト内にコメントで使用方法を記載

---

## 📄 ライセンス

このツール群はAI Family Simulatorプロジェクトの一部です。
