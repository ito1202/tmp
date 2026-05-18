# IAM / 権限設計書

## 基本方針

- キー・シークレットは使用しない。認証はすべてマネージドIDで行う
- 権限は最小権限の原則（必要なスコープ・ロールのみ付与）
- 人間の操作はすべて EntraID ユーザー経由

---

## マネージドID（サービス間認証）

| リソース | 種類 | 付与するロール | 対象スコープ | 理由 |
|---------|------|--------------|------------|------|
| app-be-test（Backend） | システムマネージドID | Cognitive Services User | Azure OpenAI リソース | FastAPI → OpenAI API 呼び出しをキーなしで行うため |
| app-be-test（Backend） | システムマネージドID | （TODO: Foundry のロール確認） | Foundry リソース | Backend → Foundry Agent との通信 |
| app-fe-test（Frontend） | システムマネージドID | （現時点では不要） | - | 今後 Backend 以外のリソースを参照する場合に追加 |

> **Note**: マネージドIDの Principal ID は `terraform output` で確認し、Azure Portal または Terraform でロールを付与する。

---

## EntraID ユーザー（人間の操作）

| 対象 | ロール | スコープ | 理由 |
|------|--------|---------|------|
| 開発者 | Contributor | リソースグループ | 構築・変更作業 |
| 運用担当者 | Reader + （個別権限） | リソースグループ | 参照・監視のみ |

> **TODO**: 本番環境では開発者の Contributor を削除し、変更は Terraform 経由のみとする

---

## リソースアクセス制御まとめ

```
[オンプレ ユーザー]
    ↓ (EntraID 認証)
[Frontend App Service]
    ↓ (VNet 内通信 / マネージドID)
[Backend App Service]
    ↓ (マネージドID)
[Azure OpenAI / Foundry]
```

---

## 未確定事項（TODO）

- [ ] Foundry が要求するロール名の確認
- [ ] EntraID のグループ設計（個人ではなくグループ単位で付与）
- [ ] 条件付きアクセスポリシーの要否（MFA など）
