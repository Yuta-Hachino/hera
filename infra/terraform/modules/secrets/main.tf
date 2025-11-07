# ==================================================
# Secret Manager - シークレット管理
# ==================================================

resource "google_secret_manager_secret" "secret" {
  secret_id = var.secret_id

  labels = var.labels

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "secret_version" {
  secret      = google_secret_manager_secret.secret.id
  secret_data = var.secret_value
}

# Cloud Runサービスアカウントにシークレットへのアクセス権限を付与
resource "google_secret_manager_secret_iam_member" "secret_access" {
  secret_id = google_secret_manager_secret.secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}
