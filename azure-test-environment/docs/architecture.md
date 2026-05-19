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
┌─ VNet  10.0.0.0/16 ──────────────────────────────────────────────────┐
│                                                                       │
│  ┌─ GatewaySubnet  10.0.255.0/27 ──────────────────────────────┐    │
│  │  VPN Gateway（Azure 仕様で名前・用途ともに固定）              │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌─ subnet-pe  10.0.2.0/24 ─────────────────────────────────────┐   │
│  │  PE: Frontend    PE: Backend    PE: Functions                 │   │
│  │  PE: Foundry     PE: Storage    PE: AI Search                 │   │
│  │  Private DNS Zone 群（各リソース対応）                         │   │
│  │                                                               │   │
│  │  役割: 外から各リソースへの「入口」を作る場所                  │   │
│  └───────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─ subnet-integration  10.0.1.0/24 ─────────────────────────── ┐   │
│  │  App Service Frontend（VNet Integration）                     │   │
│  │  App Service Backend （VNet Integration）                     │   │
│  │                                                               │   │
│  │  役割: App Service から VNet 内への「出口」                    │   │
│  │  委任: Microsoft.Web/serverFarms                              │   │
│  └───────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌─ subnet-func-integration  10.0.4.0/24 ─────────────────────── ┐  │
│  │  Azure Functions（Flex Consumption）（VNet Integration）       │  │
│  │                                                                │  │
│  │  役割: Functions から VNet 内への「出口」                       │  │
│  │  委任: Microsoft.Web/serverFarms                               │  │
│  │  ※ App Service Plan と委任名が同じでも Plan が異なるため       │  │
│  │    subnet-integration とは別 Subnet が必要                     │  │
│  └────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────┘
        ↓ Managed ID 認証（キー・シークレット不要）
【Azure マネージドゾーン】
  ├─ App Service Frontend（assistant-ui）
  ├─ App Service Backend（FastAPI）
  ├─ Azure Functions（Flex Consumption / RAG ツール）
  ├─ Storage Account（RAG 用ファイル置き場 / blob）
  ├─ Azure AI Search（RAG インデックス・ベクトル検索）
  └─ Azure AI Foundry
       ├─ 親エージェント
       ├─ 子エージェント
       ├─ GPT-5.2
       └─ Embedding 003
```

---

## Subnet の役割まとめ

| Subnet | アドレス | 役割 | 委任 | 中に置くもの |
|--------|---------|------|------|------------|
| **GatewaySubnet** | 10.0.255.0/27 | VPN Gateway 専用（名前固定） | なし | VPN Gateway のみ |
| **subnet-pe** | 10.0.2.0/24 | 外 → リソースへの「入口」 | なし | Private Endpoint 全て |
| **subnet-integration** | 10.0.1.0/24 | App Service → VNet 内の「出口」 | Microsoft.Web/serverFarms | App Service FE・BE |
| **subnet-func-integration** | 10.0.4.0/24 | Functions → VNet 内の「出口」 | Microsoft.Web/serverFarms | Azure Functions |

### Subnet を分ける理由

```
① subnet-pe と subnet-integration を分ける理由
  委任済みの Subnet に Private Endpoint は置けない（Azure 制約）

② subnet-integration と subnet-func-integration を分ける理由
  委任名が同じ（Microsoft.Web/serverFarms）でも
  App Service Plan と Flex Consumption Plan は別プランなので
  同一 Subnet を共用できない
```

---

## コンポーネント説明

| コンポーネント | 役割 |
|-------------|------|
| **VPN Gateway** | オンプレ ↔ Azure の暗号化トンネル |
| **VNet** | Azure 上のプライベートネットワーク空間 |
| **NSG** | subnet-pe のインバウンドを制御（オンプレ IP ホワイトリスト） |
| **Private Endpoint** | リソースの Public Endpoint を無効化し VNet 内プライベート IP でのみ解決 |
| **Private DNS Zone** | VNet 内で各リソースのホスト名をプライベート IP に名前解決 |
| **App Service Frontend** | assistant-ui をホスト（Public 無効） |
| **App Service Backend** | FastAPI をホスト（Public 無効）。Foundry Agent と通信 |
| **Azure Functions** | RAG ツールをホスト（Flex Consumption / Public 無効） |
| **Storage Account** | RAG 用ファイルの置き場（blob）。AI Search がインデックス作成に参照 |
| **Azure AI Search** | Storage のファイルをインデックス化。ベクトル検索を提供 |
| **Azure AI Foundry** | 親エージェント・子エージェント・GPT-5.2 / Embedding 003 を提供 |

---

## 通信フロー

### チャット回答が返るまで

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
【App Service Frontend（assistant-ui）】
  │ ④ VNet Integration（subnet-integration が出口）
  │    DNS: backend.azurewebsites.net → PE:Backend の IP
  ▼
【PE: Backend】  ─ subnet-pe 内
  │ ⑤ Azure 内部プライベート接続
  ▼
【App Service Backend（FastAPI）】
  │ ⑥ VNet Integration（subnet-integration が出口）
  │    DNS: foundry endpoint → PE:Foundry の IP
  ▼
【PE: Foundry】  ─ subnet-pe 内
  │ ⑦ Azure 内部プライベート接続 / Managed ID 認証
  ▼
【Azure AI Foundry（親エージェント）】
  │ ⑧ 推論・Tool 呼び出し
  ▼
【PE: Functions】  ─ subnet-pe 内
  │ ⑨ Azure 内部プライベート接続
  ▼
【Azure Functions（RAG ツール）】
  │ ⑩ VNet Integration（subnet-func-integration が出口）
  │    DNS: search endpoint → PE:AI Search の IP
  ▼
【PE: AI Search】  ─ subnet-pe 内
  │ ⑪ Azure 内部プライベート接続 / Managed ID 認証
  ▼
【Azure AI Search】  ← 検索結果を返す
  │ ⑫ 同じ経路を逆向きに返る
  ▼
Functions → Foundry → Backend → Frontend → オンプレ PC
```

### RAG インデックス作成（ファイル登録時）

```
【管理者がファイルをアップロード】
  │ VPN 経由 または Azure Portal 経由
  ▼
【Storage Account（blob）】
  │ AI Search がインデックス作成ジョブを実行
  ▼
【Azure AI Search】
  │ Storage の blob を読み込み
  │ Embedding 003 でベクトル化
  ▼
【インデックス完成 → 検索可能になる】
```

---

## Private Endpoint の粒度

**1 Azure リソース = 1 Private Endpoint**

| PE 名 | 接続先リソース | Private DNS Zone |
|-------|-------------|-----------------|
| PE: Frontend | App Service Frontend | `privatelink.azurewebsites.net` |
| PE: Backend | App Service Backend | `privatelink.azurewebsites.net` |
| PE: Functions | Azure Functions（Flex Consumption） | `privatelink.azurewebsites.net` |
| PE: Foundry | Azure AI Foundry | （TODO: エンドポイント確認） |
| PE: Storage | Storage Account（blob） | `privatelink.blob.core.windows.net` |
| PE: AI Search | Azure AI Search | `privatelink.search.windows.net` |

---

## 外部からの見え方

| アクセス元 | 結果 |
|----------|------|
| オンプレ（VPN 接続済み） | アクセス可能 |
| インターネット（社外） | DNS 解決不可・接続不可（存在しないと同等） |

---

## 未確定事項（TODO）

- [ ] Foundry の Private Link 対応確認（Hub / Project 単位の PE 数・DNS Zone）
- [ ] Foundry → Azure Functions 通信方式の確定（Foundry マネージドネットワーク設定）
- [ ] AI Search → Storage のプライベート接続設定（AI Search マネージド PE の要否）
- [ ] Flex Consumption の Subnet 委任名の最終確認（Microsoft.Web/serverFarms で正しいか）
- [ ] オンプレ VPN デバイスの型番・設定値
- [ ] Frontend ↔ Backend 間の認証方式
- [ ] ログ・監視設計（Azure Monitor / Log Analytics）
