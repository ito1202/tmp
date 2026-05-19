# azure-test-environment — 構築ガイド

このリポジトリは Azure 上に AI チャットアプリの閉じたインフラ環境を構築するための  
Terraform コード・設計ドキュメント一式です。

---

## このプロジェクトが作るもの

```
オンプレ PC
  │ VPN（暗号化トンネル）
  ▼
Azure（閉じたネットワーク）
  ├─ Frontend（assistant-ui）
  ├─ Backend（FastAPI）
  ├─ RAG ツール（Azure Functions）
  ├─ Storage Account（RAG 用ファイル置き場）
  ├─ Azure AI Search（ベクトル検索）
  └─ Azure AI Foundry（GPT-5.2 / エージェント）
```

社外からは存在すら見えない閉じた環境です。  
VPN で接続したオンプレのメンバーだけがアクセスできます。

---

## はじめに読む用語説明

| 用語 | 一言説明 |
|------|---------|
| **Terraform** | インフラをコードで定義・構築するツール。`terraform apply` でリソースが一括作成される |
| **リソースグループ** | Azure リソースをまとめる「フォルダ」のようなもの |
| **VNet** | Azure 上のプライベートネットワーク空間 |
| **Subnet** | VNet を役割ごとに分割した区画 |
| **Private Endpoint** | Azure サービスを VNet 内のプライベート IP でのみ使えるようにする仕組み |
| **Managed ID** | パスワード・キーなしでリソース間認証を行う Azure の仕組み |
| **tfvars** | Terraform に渡す設定値ファイル（`.env` に相当） |
| **tfstate** | Terraform が管理する「現在の状態」ファイル（手動編集禁止） |

---

## 前提条件（事前にインストールが必要なもの）

### 1. Azure CLI

```bash
# macOS
brew install azure-cli

# Windows（PowerShell）
winget install Microsoft.AzureCLI

# インストール確認
az --version
```

### 2. Terraform

```bash
# macOS
brew install terraform

# Windows（PowerShell）
winget install Hashicorp.Terraform

# インストール確認
terraform --version
# → v1.5.0 以上であること
```

### 3. Azure へのログイン

```bash
az login
# ブラウザが開く → Azure アカウントでログイン

# ログイン確認
az account show
```

---

## ファイル構成

```
azure-test-environment/
├── docs/
│   ├── architecture.pptx     # 構成図（パワポ）
│   ├── architecture.md       # 構成図の補足・通信フロー
│   └── iam-design.md         # 権限設計（誰が何にアクセスできるか）
│
├── main.tf                   # 全リソースの定義（ここを読めば何が作られるかわかる）
├── variables.tf              # 変数の定義（型・説明）
├── terraform.tfvars          # 変数の実際の値 ★要編集・gitignore 対象
├── outputs.tf                # 構築後に画面に出力される値
└── .gitignore                # tfstate・tfvars など機密ファイルを Git 管理外に
```

---

## 構築手順

### ステップ 1: terraform.tfvars を編集する

`azure-test-environment/terraform.tfvars` を開き、TODO コメントの箇所を実際の値に書き換えます。

```hcl
# 必ず変更が必要な箇所
allowed_ip_ranges = ["あなたのオンプレのグローバルIP/32"]

# Azure 全体でユニークである必要があるリソース名（他のユーザーと重複不可）
app_service_fe_name  = "世界で唯一の名前-fe"
app_service_be_name  = "世界で唯一の名前-be"
functions_app_name   = "世界で唯一の名前-func"
storage_account_name = "世界で唯一の名前"   # 小文字英数字のみ・24文字以内
ai_search_name       = "世界で唯一の名前-srch"
```

> **なぜユニークである必要があるのか**  
> App Service・Storage Account などは Azure 全体（全世界）で一意の URL になるため、  
> 他の人がすでに使っている名前は使えません。

### ステップ 2: Microsoft.App プロバイダーを登録する

Azure Functions（Flex Consumption）を使うために、一度だけ実行が必要です。

```bash
az provider register --namespace Microsoft.App
az provider show --namespace Microsoft.App --query registrationState
# → "Registered" と表示されれば OK（数分かかる場合があります）
```

### ステップ 3: Terraform を初期化する

```bash
cd azure-test-environment

terraform init
```

実行すると `.terraform/` フォルダが作られます。  
「Terraform has been successfully initialized!」と表示されれば OK です。

### ステップ 4: 作成されるリソースを確認する（実際には何も作らない）

```bash
terraform plan
```

「Plan: XX to add, 0 to change, 0 to destroy.」のように、  
これから作られるリソースの一覧が表示されます。  
エラーが出た場合はメッセージを確認して tfvars を修正してください。

### ステップ 5: リソースを作成する

```bash
terraform apply
```

「Do you want to perform these actions?」と聞かれたら `yes` と入力します。  
完了まで **20〜30 分** かかります（VPN Gateway の作成が長い）。

### ステップ 6: 作成後の確認

```bash
# VPN Gateway のパブリック IP を確認（オンプレ VPN デバイスの設定に使用）
terraform output vpn_gateway_public_ip

# Managed ID の Principal ID を確認（IAM ロール付与に使用）
terraform output backend_principal_id
terraform output functions_principal_id
```

---

## よくある注意点

### tfvars を Git にコミットしない

`terraform.tfvars` には IP アドレスなどが含まれるため `.gitignore` で除外されています。  
`git add -A` などで誤って含めないよう注意してください。

### tfstate を手動で編集しない

`terraform.tfstate` は Terraform が管理する状態ファイルです。  
手動で編集すると環境が壊れます。触らないでください。

### リソースの削除は慎重に

```bash
terraform destroy   # 全リソースを削除する（本番では絶対に実行しない）
```

---

## 構築後に必要な追加作業

Terraform だけでは完了しない設定が残っています。

| 作業 | 説明 | 参照 |
|------|------|------|
| VPN 接続設定 | オンプレ VPN デバイスに Azure VPN Gateway の IP を設定 | VPN デバイスのマニュアル |
| IAM ロール付与 | Managed ID に必要なロールを付与 | `docs/iam-design.md` |
| EntraID App Registration | Frontend・Backend 用の認証アプリを作成 | `docs/iam-design.md` |
| Foundry PE 追加 | Foundry Hub / Project の PE を追加 | `docs/architecture.md` |
| RAG ファイルのアップロード | Storage Account に PDF などを配置 | Azure Portal |

---

## 詰まったときは

- **Azure の用語がわからない** → `docs/architecture.md` を確認
- **権限エラーが出る** → `docs/iam-design.md` を確認
- **terraform apply でエラーになる** → エラーメッセージの Resource 名と変数名を照合
- **名前の重複エラー** → `terraform.tfvars` のリソース名をより一意なものに変更
