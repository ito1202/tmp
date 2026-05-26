# IAM / 権限設計書

## 基本方針

- キー・シークレットは使用しない。認証はすべてマネージド ID で行う
- 権限は最小権限の原則（必要なスコープ・ロールのみ付与）
- 人間の操作はすべて EntraID ユーザー経由
- サービス間認証はシステムマネージド ID（コード変更なしでローテーション不要）

---

## 認証フロー全体図

```
[オンプレ ユーザー]
    │ EntraID 認証（ブラウザ）
    ▼
[Frontend App Service]
    │ Bearer トークン（EntraID）
    ▼
[Backend App Service]
    │ Managed ID
    ▼
[Azure AI Foundry]
    │ Foundry Managed Network 経由
    ▼
[Azure Functions（RAG ツール）]
    │ Managed ID
    ├─▶ [Azure AI Search]
    │       │ Managed ID
    │       └─▶ [Storage Account]
    └─▶ [Storage Account]
```

---

## サービス間認証（マネージド ID）

| リソース | 付与するロール | 対象スコープ | 理由 |
|---------|--------------|------------|------|
| **Backend** | Azure AI Developer | Foundry リソース | Backend → Foundry Agent 呼び出し |
| **Functions** | Search Index Data Reader | AI Search リソース | RAG ツールでベクトル検索を実行 |
| **Functions** | Storage Blob Data Reader | Storage Account | RAG ツールでファイル参照（必要時） |
| **AI Search** | Storage Blob Data Reader | Storage Account | インデックス作成時に blob を読み込む |

> **Principal ID の確認方法**: `terraform output` で各リソースの Principal ID を取得し、  
> Azure Portal または Terraform の `azurerm_role_assignment` でロールを付与する。

---

## Frontend ↔ Backend 間の認証（EntraID）

Frontend（assistant-ui）がバックエンド API を呼ぶ際、EntraID でアクセス制御する。

```
① ユーザーがブラウザで Frontend を開く
② Frontend が EntraID（MSAL）でユーザー認証
③ Frontend が Backend の App Registration に対するアクセストークンを取得
④ Backend へのリクエストに Bearer トークンを付与
⑤ Backend が EntraID でトークンを検証 → 正規ユーザーのみ通過
```

### App Registration 設計

| App Registration | 用途 | 備考 |
|----------------|------|------|
| **frontend-app** | ユーザーがログインする入口 | Redirect URI に Frontend の URL を登録 |
| **backend-app** | Backend API のリソース定義 | frontend-app にスコープを公開する |

> **TODO**: App Registration の Client ID・Tenant ID を確定後に terraform.tfvars に追記

---

## EntraID ユーザー（人間の操作）

| 対象 | ロール | スコープ | 理由 |
|------|--------|---------|------|
| 開発者 | Contributor | リソースグループ | 構築・変更作業 |
| 運用担当者 | Reader | リソースグループ | 参照・監視のみ |
| 運用担当者 | Search Index Data Contributor | AI Search | インデックス管理 |

> 本番環境では開発者の Contributor を削除し、変更は Terraform 経由のみとする

---

## 未確定事項（TODO）

- [ ] EntraID App Registration の作成・Client ID / Tenant ID の確定
- [ ] EntraID のグループ設計（個人ではなくグループ単位でロールを付与）
- [ ] 条件付きアクセスポリシーの要否（MFA、アクセス元 IP 制限など）
- [ ] Foundry Managed Network の Managed Identity に対するロール付与手順の確認
