# アーキテクチャ設計書

> 構成図（architecture.pptx）の補足ドキュメント。
> 視覚的な図は architecture.pptx を参照。

---

## 全体構成

```
【オンプレミス】
  └─ VPN デバイス（IPsec）
        ↓ Site-to-Site VPN
【VPN Gateway】  ← GatewaySubnet 内
        ↓
┌─ VNet  10.0.0.0/16 ──────────────────────────────────────────────┐
│                                                                   │
│  ┌─ GatewaySubnet  10.0.255.0/27 ──────────────────────────┐    │
│  │  VPN Gateway（Azure 仕様で名前・用途ともに固定）          │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌─ subnet-pe  10.0.2.0/24 ──────────────────────────────── ┐   │
│  │  PE: Frontend   PE: Backend                               │   │
│  │  PE: Functions  PE: Foundry                               │   │
│  │  Private DNS Zone (privatelink.azurewebsites.net)         │   │
│  │                                                           │   │
│  │  役割: 外から各リソースへの「入口」を作る場所              │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─ subnet-integration  10.0.1.0/24 ─────────────────────── ┐   │
│  │  App Service Frontend（VNet Integration）                 │   │
│  │  App Service Backend （VNet Integration）                 │   │
│  │  Azure Functions     （VNet Integration）                 │   │
│  │                                                           │   │
│  │  役割: 各リソースから VNet 内への「出口」として使う場所    │   │
│  │  ※ 委任（Microsoft.Web/serverFarms）済み                 │   │
│  │  ※ 3 リソースが同一 App Service Plan なので Subnet 共用可 │   │
│  └───────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
        ↓ Managed ID 認証（キー・シークレット不要）
【Azure AI Foundry】
  ├─ 親エージェント
  ├─ 子エージェント
  ├─ GPT-5.2
  └─ Embedding 003
```

---

## Subnet の役割まとめ

| Subnet | アドレス | 役割 | 中に置くもの |
|--------|---------|------|------------|
| **GatewaySubnet** | 10.0.255.0/27 | VPN Gateway 専用（名前・用途 Azure 固定） | VPN Gateway のみ |
| **subnet-pe** | 10.0.2.0/24 | 外 → リソースへの「入口」 | Private Endpoint（PE）全て |
| **subnet-integration** | 10.0.1.0/24 | リソース → VNet 内への「出口」 | App Service・Functions（VNet Integration） |

### なぜ subnet-pe と subnet-integration を分けるか

Azure の制約として、VNet Integration に使う Subnet（委任あり）と
Private Endpoint を置く Subnet は同一にできない。

```
subnet-integration: 委任あり → Private Endpoint を置けない
subnet-pe:          委任なし → Private Endpoint を複数置ける
```

---

## コンポーネント説明

| コンポーネント | 役割 |
|-------------|------|
| **VPN Gateway** | オンプレ ↔ Azure の暗号化トンネル |
| **VNet** | Azure 上のプライベートネットワーク空間 |
| **NSG** | subnet-pe のインバウンドを制御（オンプレ IP ホワイトリスト） |
| **Private Endpoint** | リソースの Public URL を無効化し VNet 内プライベート IP でのみ解決 |
| **Private DNS Zone** | VNet 内で `*.azurewebsites.net` をプライベート IP に名前解決 |
| **App Service Frontend** | assistant-ui をホスト（Public 無効） |
| **App Service Backend** | FastAPI をホスト（Public 無効）。Foundry Agent と通信 |
| **Azure Functions** | Tool / MCP サーバーをホスト（Public 無効） |
| **Azure AI Foundry** | 親エージェント・子エージェント・GPT-5.2 / Embedding 003 を提供 |

---

## 通信フロー（チャット回答が返るまで）

```
【オンプレ PC】
  │ ① VPN（IPsec）
  ▼
【VPN Gateway】  ─ GatewaySubnet 内
  │ ② VNet に入る
  ▼
【PE: Frontend】  ─ subnet-pe 内
  │ ③ Azure 内部プライベート接続
  ▼
【App Service Frontend】  ─ Azure マネージドゾーン（VNet 外）
  │ ④ VNet Integration で VNet に出る（subnet-integration が出口）
  │    Private DNS: frontend → PE:Backend のプライベート IP に解決
  ▼
【PE: Backend】  ─ subnet-pe 内
  │ ⑤ Azure 内部プライベート接続
  ▼
【App Service Backend（FastAPI）】  ─ Azure マネージドゾーン
  │ ⑥ VNet Integration で VNet に出る（subnet-integration が出口）
  │    Private DNS: foundry → PE:Foundry のプライベート IP に解決
  ▼
【PE: Foundry】  ─ subnet-pe 内
  │ ⑦ Azure 内部プライベート接続 / Managed ID 認証
  ▼
【Azure AI Foundry】
  │ ⑧ 親エージェントが推論
  │    必要に応じて子エージェント・Tool を呼ぶ
  │    Tool 呼び出し時: Foundry → PE:Functions → Azure Functions
  ▼
  回答生成
  │ ⑨ 同じ経路を逆向きに返る
  ▼
Backend → Frontend → オンプレ PC
```

---

## Private Endpoint の粒度

**1 Azure リソース = 1 Private Endpoint**

| PE 名 | 接続先リソース | 備考 |
|-------|-------------|------|
| PE: Frontend | App Service Frontend | |
| PE: Backend | App Service Backend | |
| PE: Functions | Azure Functions | Functions App が複数あれば PE も複数必要 |
| PE: Foundry | Azure AI Foundry | Foundry Hub / Project で増える場合あり（TODO） |

---

## 外部からの見え方

| アクセス元 | 結果 |
|----------|------|
| オンプレ（VPN 接続済み） | アクセス可能 |
| インターネット（社外） | DNS 解決不可・接続不可（存在しないと同等） |

---

## 未確定事項（TODO）

- [ ] Foundry の Private Link 対応確認（Hub / Project 単位の PE 数）
- [ ] Foundry → Azure Functions 通信方式の確定（Foundry マネージドネットワーク設定）
- [ ] Azure Functions の App 分割数（Tool / MCP を 1 App にまとめるか分けるか）
- [ ] オンプレ VPN デバイスの型番・設定値
- [ ] Frontend ↔ Backend 間の認証方式
- [ ] ログ・監視設計（Azure Monitor / Log Analytics）
