# アーキテクチャ設計書

> 構成図（architecture.pptx）の補足ドキュメント。
> 視覚的な図は architecture.pptx を参照。

---

## 全体構成

```
[オンプレミス]
  └─ VPN デバイス（IPsec）
        ↓ Site-to-Site VPN
[Azure VPN Gateway]
        ↓
[VNet: 10.0.0.0/16]
  ├─ GatewaySubnet: 10.0.255.0/27  ← VPN Gateway 専用
  └─ subnet-app:    10.0.1.0/24
       ├─ Private Endpoint → App Service Frontend
       ├─ Private Endpoint → App Service Backend
       └─ Private DNS Zone (privatelink.azurewebsites.net)

[App Service Frontend]  ─(VNet Integration)→  subnet-app
[App Service Backend]   ─(VNet Integration)→  subnet-app
  └─ マネージドID で Azure OpenAI / Foundry に接続
```

---

## コンポーネント説明

| コンポーネント | 役割 |
|-------------|------|
| **VPN Gateway** | オンプレ ↔ Azure の暗号化トンネル |
| **VNet** | Azure 上のプライベートネットワーク空間 |
| **NSG** | Subnet レベルのインバウンド制御（IPホワイトリスト） |
| **Private Endpoint** | App Service の Public URL を無効化し VNet 内 IP でのみ解決 |
| **Private DNS Zone** | VNet 内で `*.azurewebsites.net` をプライベートIPに名前解決 |
| **App Service Frontend** | assistant-ui をホスト |
| **App Service Backend** | FastAPI をホスト。Foundry Agent と通信 |
| **Foundry / Azure OpenAI** | GPT-5.2 / Embedding 003 を提供 |

---

## 通信フロー

### ユーザー → Frontend

```
オンプレ PC → VPN → VPN Gateway → VNet → Private Endpoint → Frontend App Service
```

### Frontend → Backend

```
Frontend → VNet 内通信 → Backend App Service
```

### Backend → AI

```
Backend → マネージドID 認証 → Foundry / Azure OpenAI
```

---

## 外部からの見え方

| アクセス元 | 結果 |
|----------|------|
| オンプレ（VPN 接続済み） | アクセス可能 |
| インターネット（社外） | DNS 解決不可・接続不可（存在しないと同等） |

---

## 未確定事項（TODO）

- [ ] Foundry のエンドポイント形式（Private Link 対応の有無）
- [ ] オンプレ VPN デバイスの型番・設定値
- [ ] Frontend ↔ Backend 間の認証方式
- [ ] ログ・監視設計（Azure Monitor / Log Analytics）
