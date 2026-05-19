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

## 段階的構築（推奨）

いきなり全部を `terraform apply` するのではなく、フェーズごとに確認しながら進めます。  
各フェーズで `-target` フラグを使い、対象リソースだけを作成します。

> **なぜ段階的にするのか**  
> 問題が起きたとき「どこで壊れたか」が特定しやすくなるためです。  
> また VPN Gateway（作成 20〜30 分・月額 $32）など重いリソースは  
> 後回しにすることでコストと時間を節約できます。

---

### フェーズ 1: ネットワーク基盤

**何をするか**: リソースグループ・VNet・Subnet・NSG を作る。全リソースの土台。

```bash
terraform apply \
  -target=azurerm_resource_group.main \
  -target=azurerm_virtual_network.main \
  -target=azurerm_subnet.gateway \
  -target=azurerm_subnet.pe \
  -target=azurerm_subnet.integration \
  -target=azurerm_subnet.func_integration \
  -target=azurerm_network_security_group.app \
  -target=azurerm_subnet_network_security_group_association.pe
```

**確認**: Azure Portal でリソースグループ `ito1202` に VNet と Subnet が 4 つ作られていれば OK。

---

### フェーズ 2: Backend App Service（閉域化確認）

**何をするか**: Backend だけを建てて「社外から見えないか」を確認する。  
これが通れば閉域化の仕組みは正しく動いている。

```bash
terraform apply \
  -target=azurerm_service_plan.main \
  -target=azurerm_linux_web_app.backend \
  -target=azurerm_app_service_virtual_network_swift_connection.backend \
  -target=azurerm_private_dns_zone.app_service \
  -target=azurerm_private_dns_zone_virtual_network_link.app_service \
  -target=azurerm_private_endpoint.backend
```

**確認**:

```bash
# ① プライベート IP が払い出されているか
terraform output backend_private_ip
# → 10.0.2.x が返れば OK

# ② 自分の PC（社外扱い）から繋がらないか
curl https://<app_service_be_name>.azurewebsites.net
# → 「Could not resolve host」または接続タイムアウト → ✓ 閉じている
```

---

### フェーズ 3: Frontend App Service

**何をするか**: Frontend を建てて Backend と繋がるか確認する。

```bash
terraform apply \
  -target=azurerm_linux_web_app.frontend \
  -target=azurerm_app_service_virtual_network_swift_connection.frontend \
  -target=azurerm_private_endpoint.frontend
```

**確認**:

```bash
terraform output frontend_private_ip
# → 10.0.2.x が返れば OK
```

---

### フェーズ 4: VPN Gateway

**何をするか**: オンプレと Azure を VPN トンネルで繋ぐ。  
**前提**: オンプレ VPN デバイスの型番・グローバル IP が確定していること。

```bash
terraform apply \
  -target=azurerm_public_ip.vpn_gateway \
  -target=azurerm_virtual_network_gateway.main
```

> 作成に **20〜30 分** かかります。

作成後、`terraform output vpn_gateway_public_ip` で Azure 側の IP を確認し、  
オンプレ VPN デバイスに設定します（デバイスのマニュアルを参照）。

その後、`main.tf` の以下のコメントアウトを外して apply します:
```hcl
# resource "azurerm_local_network_gateway" "onprem" {}
# resource "azurerm_virtual_network_gateway_connection" "onprem" {}
```

**確認**:

```bash
# VPN 接続後、オンプレ PC から以下が通れば成功
curl https://<app_service_be_name>.azurewebsites.net
# → フェーズ 2 では繋がらなかったが、VPN 経由では 200 が返る
```

---

### フェーズ 5: Azure Functions（RAG ツール）

**何をするか**: Functions を建てて VNet 内の AI Search を呼べる出口を作る。

```bash
terraform apply \
  -target=azurerm_service_plan.functions \
  -target=azurerm_storage_account.functions \
  -target=azurerm_linux_function_app.main \
  -target=azurerm_app_service_virtual_network_swift_connection.functions \
  -target=azurerm_private_endpoint.functions
```

---

### フェーズ 6: Storage Account・Azure AI Search（RAG 基盤）

**何をするか**: RAG 用のファイル置き場と検索エンジンを建てる。

```bash
terraform apply \
  -target=azurerm_storage_account.main \
  -target=azurerm_private_dns_zone.storage_blob \
  -target=azurerm_private_dns_zone_virtual_network_link.storage_blob \
  -target=azurerm_private_endpoint.storage \
  -target=azurerm_search_service.main \
  -target=azurerm_private_dns_zone.ai_search \
  -target=azurerm_private_dns_zone_virtual_network_link.ai_search \
  -target=azurerm_private_endpoint.ai_search
```

**確認**: Azure Portal で Storage Account と AI Search が作成されていること。  
Storage Account に blob コンテナを作成し、テスト用ファイルをアップロードする。

---

### フェーズ 7: 監視（Log Analytics）

**何をするか**: 各リソースのログを一か所に集約する。

```bash
terraform apply \
  -target=azurerm_log_analytics_workspace.main \
  -target=azurerm_monitor_diagnostic_setting.frontend \
  -target=azurerm_monitor_diagnostic_setting.backend \
  -target=azurerm_monitor_diagnostic_setting.functions \
  -target=azurerm_monitor_diagnostic_setting.ai_search
```

---

### フェーズ 8: Foundry（Foundry リソース確定後）

**何をするか**: Foundry Hub・Project の Private Endpoint を追加する。  
**前提**: Foundry Hub と Project が Azure Portal で作成済みであること。

`main.tf` のコメントアウトを外してリソース ID を埋めてから apply します:
```hcl
# resource "azurerm_private_endpoint" "foundry_hub" { ... }
# resource "azurerm_private_endpoint" "foundry_project" { ... }
```

---

### 全フェーズ完了後の追加作業

| 作業 | タイミング |
|------|-----------|
| Managed ID へのロール付与 | フェーズ 5・6 完了後 |
| EntraID App Registration 作成 | フェーズ 3 完了後 |
| Foundry Managed Network 設定 | フェーズ 8 完了後 |
| RAG ファイルのアップロード | フェーズ 6 完了後 |

詳細は `docs/iam-design.md` を参照してください。

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
