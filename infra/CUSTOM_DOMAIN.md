# カスタムドメイン設定ガイド

Cloud RunサービスにカスタムドメインをTerraformで設定する方法です。

## 前提条件

- ドメインを所有していること (例: example.com)
- ドメインのDNS設定を変更できること
- Google Search Consoleでドメインの所有権確認ができること

## Step 1: ドメインの所有権確認

### Google Search Consoleでの確認

1. [Google Search Console](https://search.google.com/search-console) にアクセス
2. プロパティを追加
3. ドメイン名を入力 (例: `example.com`)
4. DNS TXTレコードを追加して所有権を確認

### TXTレコードの追加例

```
Type: TXT
Name: @
Value: google-site-verification=xxxxxxxxxxxxx
```

## Step 2: Terraform設定ファイルの編集

`terraform.tfvars` にカスタムドメイン設定を追加:

```hcl
# カスタムドメインを有効化
custom_domain_enabled = true

# フロントエンドのドメイン
frontend_domain = "app.example.com"

# バックエンドAPIのドメイン
backend_domain = "api.example.com"
```

## Step 3: Terraformでデプロイ

```bash
cd infra/terraform

# 変更内容を確認
terraform plan -var-file=environments/prod/terraform.tfvars

# デプロイ
terraform apply -var-file=environments/prod/terraform.tfvars
```

デプロイが完了すると、設定すべきDNSレコードが出力されます:

```bash
terraform output dns_records
```

## Step 4: DNSレコードの設定

### Terraform出力から取得

```bash
terraform output dns_records
```

出力例:
```json
{
  "frontend": {
    "type": "CNAME",
    "name": "app.example.com",
    "value": "ghs.googlehosted.com"
  },
  "backend": {
    "type": "CNAME",
    "name": "api.example.com",
    "value": "ghs.googlehosted.com"
  }
}
```

### DNSプロバイダーでの設定

お使いのDNSプロバイダー (Cloudflare, Route 53, Google Domainsなど) で以下のレコードを追加:

#### Frontend

```
Type: CNAME
Name: app
Host: app.example.com
Value: ghs.googlehosted.com
TTL: 3600
```

#### Backend

```
Type: CNAME
Name: api
Host: api.example.com
Value: ghs.googlehosted.com
TTL: 3600
```

## Step 5: SSL証明書の自動プロビジョニング

- Google CloudがSSL証明書を自動的にプロビジョニングします
- DNS設定が正しければ、通常 **15分〜1時間** で完了
- 証明書は自動的に更新されます

## 確認

### DNS伝播の確認

```bash
# Linuxの場合
dig app.example.com

# macOSの場合
nslookup app.example.com

# Windows (PowerShell)
Resolve-DnsName app.example.com
```

### SSL証明書の確認

```bash
curl -I https://app.example.com
```

### ブラウザでアクセス

1. `https://app.example.com` にアクセス
2. 鍵マークをクリックして証明書を確認

## トラブルシューティング

### エラー: "Domain ownership verification failed"

**原因**: ドメインの所有権が確認されていない

**解決方法**:
1. Google Search Consoleでドメインを確認
2. DNS TXTレコードが正しく設定されているか確認
3. DNS伝播を待つ (最大48時間)

### エラー: "SSL certificate provisioning failed"

**原因**: DNS設定が正しくない、またはDNS伝播中

**解決方法**:
```bash
# DNSレコードを確認
dig CNAME app.example.com

# 出力が "ghs.googlehosted.com" を指していることを確認
```

### SSL証明書がプロビジョニングされない

**原因**: DNS伝播に時間がかかっている

**解決方法**:
- 最大24時間待つ
- Cloud Consoleでステータスを確認:
  ```bash
  gcloud run domain-mappings describe \
    --domain=app.example.com \
    --region=asia-northeast1
  ```

## ドメイン削除

カスタムドメインを削除する場合:

```hcl
# terraform.tfvars
custom_domain_enabled = false
```

```bash
terraform apply -var-file=environments/prod/terraform.tfvars
```

## サブドメインの追加

複数のサブドメインを使用する例:

```hcl
# 本番環境
frontend_domain = "app.example.com"
backend_domain = "api.example.com"

# ステージング環境 (別の環境変数ファイル)
frontend_domain = "staging.example.com"
backend_domain = "api-staging.example.com"
```

## Cloudflare使用時の注意点

Cloudflareを使用している場合:

1. **DNS設定**: CloudflareのDNS管理画面でCNAMEレコードを追加
2. **SSL/TLS設定**: "Full" または "Full (strict)" に設定
3. **Proxy状態**: オレンジ雲マーク（Proxied）ではなく、グレー雲マーク（DNS only）に設定
   - Cloud RunのSSL証明書を使用するため

## 参考資料

- [Cloud Run カスタムドメインのマッピング](https://cloud.google.com/run/docs/mapping-custom-domains)
- [Google Search Console](https://search.google.com/search-console)
- [DNS伝播チェックツール](https://www.whatsmydns.net/)
