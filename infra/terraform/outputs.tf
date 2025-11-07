# ==================================================
# 出力
# ==================================================

output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP Region"
  value       = var.region
}

output "environment" {
  description = "Environment"
  value       = var.environment
}

# ==================================================
# Cloud Run URLs
# ==================================================

output "backend_url" {
  description = "Backend Cloud Run URL"
  value       = module.backend.service_url
}

output "frontend_url" {
  description = "Frontend Cloud Run URL"
  value       = module.frontend.service_url
}

# output "adk_url" {
#   description = "ADK Cloud Run URL"
#   value       = module.adk.service_url
# }

# ==================================================
# Service Account
# ==================================================

output "service_account_email" {
  description = "Cloud Run service account email"
  value       = google_service_account.cloud_run.email
}

# ==================================================
# カスタムドメイン情報
# ==================================================

output "custom_domain_enabled" {
  description = "Whether custom domain is enabled"
  value       = var.custom_domain_enabled
}

output "frontend_custom_domain" {
  description = "Frontend custom domain"
  value       = var.custom_domain_enabled && var.frontend_domain != "" ? var.frontend_domain : null
}

output "backend_custom_domain" {
  description = "Backend custom domain"
  value       = var.custom_domain_enabled && var.backend_domain != "" ? var.backend_domain : null
}

output "dns_records" {
  description = "DNS records to configure for custom domains"
  value = var.custom_domain_enabled ? {
    frontend = var.frontend_domain != "" ? {
      type  = "CNAME"
      name  = var.frontend_domain
      value = "ghs.googlehosted.com"
      note  = "Google-managed SSL certificate will be provisioned automatically"
    } : null
    backend = var.backend_domain != "" ? {
      type  = "CNAME"
      name  = var.backend_domain
      value = "ghs.googlehosted.com"
      note  = "Google-managed SSL certificate will be provisioned automatically"
    } : null
  } : null
}

# ==================================================
# 次のステップ
# ==================================================

output "next_steps" {
  description = "Next steps after deployment"
  value = <<-EOT

  ========================================
  デプロイ完了！
  ========================================

  Frontend URL: ${module.frontend.service_url}
  Backend URL:  ${module.backend.service_url}

  次のステップ:
  1. Frontend URLにアクセスしてアプリを確認
  2. Firebase Consoleで認証のリダイレクトURIを追加:
     https://console.firebase.google.com/project/${var.firebase_project_id}/authentication/providers
     - 承認済みドメインに追加: ${replace(module.frontend.service_url, "https://", "")}
  3. サービスアカウントに権限を付与:
     - hera-cloud-run-prod@gen-lang-client-0830629645.iam.gserviceaccount.com に
       roles/firebase.admin と roles/storage.admin を付与してください

  EOT
}
