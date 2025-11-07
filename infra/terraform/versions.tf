terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  # Terraform State をGCS バケットに保存する設定
  # 初回は backend {} をコメントアウトしてローカルで terraform init を実行
  # その後、GCSバケットを作成してから以下をコメントインして terraform init -migrate-state
  # backend "gcs" {
  #   bucket = "hera-terraform-state"
  #   prefix = "terraform/state"
  # }
}
