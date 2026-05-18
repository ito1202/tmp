# azure-test-environment

Azure 最小構成のインフラ定義（Terraform）。

## ドキュメント

| ドキュメント | 場所 | 内容 |
|------------|------|------|
| 構成図 | `docs/architecture.pptx` | 全体アーキテクチャ（パワポ） |
| アーキテクチャ補足 | `docs/architecture.md` | 構成図のテキスト補足・通信フロー |
| IAM設計書 | `docs/iam-design.md` | 権限設計・マネージドID |

## ディレクトリ構成

```
azure-test-environment/
├── docs/
│   ├── architecture.pptx   # 構成図
│   ├── architecture.md     # アーキテクチャ補足
│   └── iam-design.md       # IAM・権限設計
├── main.tf                 # リソース定義
├── variables.tf            # 変数定義
├── terraform.tfvars        # 設定値（gitignore 対象）
├── outputs.tf              # 構築後の出力値
└── .gitignore
```

## 構築手順

### 前提

- Terraform v1.5 以上
- Azure CLI でログイン済み（`az login`）
- `terraform.tfvars` に実際の値を設定済み

### 手順

```bash
# 1. 初期化
terraform init

# 2. 差分確認
terraform plan

# 3. 適用
terraform apply
```

### 構築後の確認

```bash
# VPN Gateway の Public IP（オンプレ VPN 設定に使用）
terraform output vpn_gateway_public_ip

# マネージドID の Principal ID（IAM ロール付与に使用）
terraform output backend_principal_id
```

## TODO

- [ ] `docs/architecture.pptx` の作成
- [ ] オンプレ VPN デバイスの設定（`azurerm_local_network_gateway` / `azurerm_virtual_network_gateway_connection`）
- [ ] Foundry リソースの追加
- [ ] マネージドID へのロール付与
- [ ] Terraform リモートステートの設定（Azure Storage）
