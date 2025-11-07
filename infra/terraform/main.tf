# ==================================================
# サービスアカウント
# ==================================================
# Note: 必要なAPIは事前に有効化済み
# - run.googleapis.com
# - cloudbuild.googleapis.com
# - artifactregistry.googleapis.com
# - secretmanager.googleapis.com
# - iam.googleapis.com

resource "google_service_account" "cloud_run" {
  account_id   = "hera-cloud-run-${var.environment}"
  display_name = "Hera Cloud Run Service Account (${var.environment})"
  description  = "Service account for Hera Cloud Run services"
}

# Firebaseへのアクセス権限を付与
# Note: 以下のIAMリソースはCloud Resource Manager APIの権限が必要なためコメントアウト
# 手動でGCP Consoleから設定が必要:
# - hera-cloud-run-prod@gen-lang-client-0830629645.iam.gserviceaccount.com に
#   roles/firebase.admin と roles/storage.admin を付与してください
#
# resource "google_project_iam_member" "firebase_admin" {
#   project = var.project_id
#   role    = "roles/firebase.admin"
#   member  = "serviceAccount:${google_service_account.cloud_run.email}"
# }

# resource "google_project_iam_member" "storage_admin" {
#   project = var.project_id
#   role    = "roles/storage.admin"
#   member  = "serviceAccount:${google_service_account.cloud_run.email}"
# }

# ==================================================
# Secret Manager - シークレット作成
# ==================================================

module "secret_gemini_api_key" {
  source = "./modules/secrets"

  secret_id             = "gemini-api-key-${var.environment}"
  secret_value          = var.gemini_api_key
  service_account_email = google_service_account.cloud_run.email
  labels                = var.labels
}

module "secret_firebase_api_key" {
  source = "./modules/secrets"

  secret_id             = "firebase-api-key-${var.environment}"
  secret_value          = var.firebase_api_key
  service_account_email = google_service_account.cloud_run.email
  labels                = var.labels
}

# ==================================================
# Cloud Run - Backend Service
# ==================================================

module "backend" {
  source = "./modules/cloud-run"

  service_name = "${var.backend_service_name}-${var.environment}"
  region       = var.region
  image        = "${var.region}-docker.pkg.dev/${var.project_id}/hera/${var.backend_service_name}:latest"

  container_port = 8080
  cpu            = var.backend_cpu
  memory         = var.backend_memory
  timeout        = 300

  min_instances = var.min_instances
  max_instances = var.max_instances

  env_vars = {
    SESSION_TYPE            = "firebase"
    STORAGE_MODE            = "firebase"
    FLASK_DEBUG             = "False"
    ALLOWED_ORIGINS         = "*"  # Will be updated in Phase 3 with actual Frontend URL
    FIREBASE_STORAGE_BUCKET = var.firebase_storage_bucket
  }

  secret_env_vars = {
    GEMINI_API_KEY = {
      secret  = module.secret_gemini_api_key.secret_name
      version = "latest"
    }
  }

  service_account_email  = google_service_account.cloud_run.email
  allow_unauthenticated  = true
  labels                 = var.labels

  depends_on = [
    module.secret_gemini_api_key
  ]
}

# ==================================================
# Cloud Run - Frontend Service
# ==================================================

module "frontend" {
  source = "./modules/cloud-run"

  service_name = "${var.frontend_service_name}-${var.environment}"
  region       = var.region
  image        = "${var.region}-docker.pkg.dev/${var.project_id}/hera/${var.frontend_service_name}:latest"

  container_port = 3000
  cpu            = var.frontend_cpu
  memory         = var.frontend_memory
  timeout        = 60

  min_instances = var.min_instances
  max_instances = var.max_instances

  env_vars = {
    NEXT_PUBLIC_API_URL                        = module.backend.service_url
    NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN           = var.firebase_auth_domain
    NEXT_PUBLIC_FIREBASE_PROJECT_ID            = var.firebase_project_id
    NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET        = var.firebase_storage_bucket
    NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID   = var.firebase_messaging_sender_id
    NEXT_PUBLIC_FIREBASE_APP_ID                = var.firebase_app_id
  }

  secret_env_vars = {
    NEXT_PUBLIC_FIREBASE_API_KEY = {
      secret  = module.secret_firebase_api_key.secret_name
      version = "latest"
    }
  }

  service_account_email  = google_service_account.cloud_run.email
  allow_unauthenticated  = true
  labels                 = var.labels

  depends_on = [
    module.backend,
    module.secret_firebase_api_key
  ]
}

# ==================================================
# Cloud Run - ADK Service
# ==================================================
# Note: ADK Dockerイメージをまだビルドしていないためコメントアウト
# ADKをデプロイする場合は、deploy-script.shでADKイメージをビルド＆プッシュしてからコメント解除してください
#
# module "adk" {
#   source = "./modules/cloud-run"
#
#   service_name = "${var.adk_service_name}-${var.environment}"
#   region       = var.region
#   image        = "${var.region}-docker.pkg.dev/${var.project_id}/hera/${var.adk_service_name}:latest"
#
#   container_port = 8000
#   cpu            = var.adk_cpu
#   memory         = var.adk_memory
#   timeout        = 600
#
#   min_instances = var.min_instances
#   max_instances = 5
#
#   env_vars = {
#     SESSION_TYPE = "firebase"
#     STORAGE_MODE = "firebase"
#   }
#
#   secret_env_vars = {
#     GEMINI_API_KEY = {
#       secret  = module.secret_gemini_api_key.secret_name
#       version = "latest"
#     }
#   }
#
#   service_account_email  = google_service_account.cloud_run.email
#   allow_unauthenticated  = true
#   labels                 = var.labels
#
#   depends_on = [
#     module.secret_gemini_api_key
#   ]
# }

# ==================================================
# ランダムなサフィックスを生成（URL用）
# ==================================================

resource "random_id" "suffix" {
  byte_length = 4
}

# ==================================================
# カスタムドメインマッピング
# ==================================================

# Frontend カスタムドメイン
resource "google_cloud_run_domain_mapping" "frontend" {
  count = var.custom_domain_enabled && var.frontend_domain != "" ? 1 : 0

  location = var.region
  name     = var.frontend_domain

  metadata {
    namespace = var.project_id
    labels    = var.labels
  }

  spec {
    route_name = module.frontend.service_name
  }

  depends_on = [module.frontend]
}

# Backend カスタムドメイン
resource "google_cloud_run_domain_mapping" "backend" {
  count = var.custom_domain_enabled && var.backend_domain != "" ? 1 : 0

  location = var.region
  name     = var.backend_domain

  metadata {
    namespace = var.project_id
    labels    = var.labels
  }

  spec {
    route_name = module.backend.service_name
  }

  depends_on = [module.backend]
}
