# ==================================================
# Cloud Run Service
# ==================================================

resource "google_cloud_run_v2_service" "service" {
  name     = var.service_name
  location = var.region

  labels = var.labels

  template {
    containers {
      image = var.image

      # リソース設定
      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }

      # 環境変数
      dynamic "env" {
        for_each = var.env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      # Secret Manager からの環境変数
      dynamic "env" {
        for_each = var.secret_env_vars
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value.secret
              version = env.value.version
            }
          }
        }
      }

      # ポート設定
      ports {
        container_port = var.container_port
      }
    }

    # スケーリング設定
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    # タイムアウト設定
    timeout = "${var.timeout}s"

    # サービスアカウント
    service_account = var.service_account_email
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# ==================================================
# IAM - 認証なしアクセスを許可
# ==================================================

resource "google_cloud_run_v2_service_iam_member" "noauth" {
  count = var.allow_unauthenticated ? 1 : 0

  name     = google_cloud_run_v2_service.service.name
  location = google_cloud_run_v2_service.service.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
