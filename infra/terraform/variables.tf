# ==================================================
# プロジェクト基本設定
# ==================================================

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-northeast1"
}

variable "environment" {
  description = "Environment (dev/prod)"
  type        = string
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be 'dev' or 'prod'."
  }
}

# ==================================================
# Cloud Run 設定
# ==================================================

variable "backend_service_name" {
  description = "Backend Cloud Run service name"
  type        = string
  default     = "hera-backend"
}

variable "frontend_service_name" {
  description = "Frontend Cloud Run service name"
  type        = string
  default     = "hera-frontend"
}

variable "adk_service_name" {
  description = "ADK Cloud Run service name"
  type        = string
  default     = "hera-adk"
}

variable "backend_memory" {
  description = "Backend service memory allocation"
  type        = string
  default     = "1Gi"
}

variable "backend_cpu" {
  description = "Backend service CPU allocation"
  type        = string
  default     = "1"
}

variable "frontend_memory" {
  description = "Frontend service memory allocation"
  type        = string
  default     = "1Gi"
}

variable "frontend_cpu" {
  description = "Frontend service CPU allocation"
  type        = string
  default     = "1"
}

variable "adk_memory" {
  description = "ADK service memory allocation"
  type        = string
  default     = "2Gi"
}

variable "adk_cpu" {
  description = "ADK service CPU allocation"
  type        = string
  default     = "2"
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

# ==================================================
# 環境変数 (Secret Managerで管理)
# ==================================================

variable "gemini_api_key" {
  description = "Gemini API Key"
  type        = string
  sensitive   = true
}

variable "firebase_api_key" {
  description = "Firebase API Key"
  type        = string
  sensitive   = true
}

variable "firebase_auth_domain" {
  description = "Firebase Auth Domain"
  type        = string
}

variable "firebase_project_id" {
  description = "Firebase Project ID"
  type        = string
}

variable "firebase_storage_bucket" {
  description = "Firebase Storage Bucket"
  type        = string
}

variable "firebase_messaging_sender_id" {
  description = "Firebase Messaging Sender ID"
  type        = string
}

variable "firebase_app_id" {
  description = "Firebase App ID"
  type        = string
}

# ==================================================
# カスタムドメイン (オプション)
# ==================================================

variable "custom_domain_enabled" {
  description = "Enable custom domain mapping"
  type        = bool
  default     = false
}

variable "frontend_domain" {
  description = "Custom domain for frontend (e.g., app.example.com)"
  type        = string
  default     = ""
}

variable "backend_domain" {
  description = "Custom domain for backend API (e.g., api.example.com)"
  type        = string
  default     = ""
}

# ==================================================
# タグとラベル
# ==================================================

variable "labels" {
  description = "Labels to apply to resources"
  type        = map(string)
  default = {
    application = "hera"
    managed_by  = "terraform"
  }
}
