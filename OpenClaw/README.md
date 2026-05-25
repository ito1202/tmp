# OpenClaw セットアップ手順（Azure VM + Azure OpenAI）

AIセキュリティプラットフォームの検証環境として、Azure VM上にOpenClawをセットアップする手順です。

---

## 前提条件

| 項目 | 要件 |
|------|------|
| OS | Windows 11 または Ubuntu 22.04 (Azure VM) |
| Node.js | v22.19+ または v24.x（推奨） |
| パッケージマネージャー | npm / pnpm / bun いずれか |
| Azure OpenAI | デプロイ済みモデルのエンドポイント・APIキー |

### Node.js バージョン確認

```bash
node --version
# v22.x.x 以上であること
```

Node.js が未インストールまたはバージョンが古い場合は [nvm](https://github.com/nvm-sh/nvm)（Linux）または [winget](https://winget.run/)（Windows）でインストールする。

```bash
# Linux (nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
nvm install 24
nvm use 24

# Windows (winget)
winget install OpenJS.NodeJS.LTS
```

---

## 1. OpenClaw インストール

```bash
npm install -g openclaw@latest
```

インストール確認：

```bash
openclaw --version
```

---

## 2. 初期セットアップ（オンボーディング）

```bash
openclaw onboard --install-daemon
```

ウィザードが起動し、以下を対話形式で設定します：

- ゲートウェイ（LLMプロバイダー接続）
- ワークスペース
- チャンネル
- スキル（シェル実行、ファイルI/O、ブラウザ操作など）

> ウィザードを完了しなくても、後述の設定ファイルを直接編集することで Azure OpenAI に接続可能です。

---

## 3. Azure OpenAI 接続設定

### 3-1. 設定ファイルの場所

| OS | パス |
|----|------|
| Linux / macOS | `~/.openclaw/openclaw.json` |
| Windows | `%USERPROFILE%\.openclaw\openclaw.json` |

### 3-2. Azure OpenAI 情報の確認

Azure Portal → Azure OpenAI リソース → 「キーとエンドポイント」から取得：

| 項目 | 例 |
|------|----|
| エンドポイント | `https://<resource-name>.openai.azure.com` |
| APIキー | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| デプロイ名 | `gpt-4o`（Portalで作成したデプロイの名前） |
| APIバージョン | `2024-12-01-preview` |

### 3-3. 設定ファイルの記述

`~/.openclaw/openclaw.json` を以下の内容で作成・編集します：

```json
{
  "agent": {
    "model": "openai/<your-deployment-name>"
  },
  "models": {
    "providers": {
      "openai": {
        "baseUrl": "https://<your-resource-name>.openai.azure.com",
        "apiKey": "<your-azure-openai-api-key>"
      }
    }
  }
}
```

**設定のポイント：**

- `baseUrl` を `*.openai.azure.com` にすると OpenClaw が Azure エンドポイントを自動検出し、以下を自動処理します：
  - 認証ヘッダーを `Authorization: Bearer` → `api-key: <key>` に切替
  - リクエストパスを `/openai/deployments/{deployment}/...` 形式に変換
  - APIバージョンクエリパラメータを自動付与
- `model` の値は **デプロイ名**（モデル識別子ではなく Portal で設定した名前）を指定

### 3-4. APIバージョンの指定（任意）

```bash
# Linux / macOS
export AZURE_OPENAI_API_VERSION="2024-12-01-preview"

# Windows (PowerShell)
$env:AZURE_OPENAI_API_VERSION = "2024-12-01-preview"
```

デフォルト値は `2024-12-01-preview` です。

---

## 4. 動作確認

```bash
openclaw
```

チャット画面が起動したら、任意のメッセージを送信してレスポンスが返れば接続成功です。

---

## 5. セキュリティ検証（AIレッドチーム用途）

本環境は AIセキュリティプラットフォームの製品検証として、OpenClaw エージェントに対するセキュリティテストを目的としています。

### 検証対象の主なリスク

| カテゴリ | 内容 |
|----------|------|
| プロンプトインジェクション | 悪意ある入力によるシェルコマンド実行誘導 |
| 過剰権限実行 | スキル（ファイルI/O・ネット）の不正利用 |
| 認証情報漏洩 | メモリや設定ファイルからのAPIキー抽出 |
| サンドボックス逸脱 | コンテナ・VM境界を越えた操作 |

### 推奨テストツール

| ツール | 用途 |
|--------|------|
| [SuperClaw](https://github.com/Shashikant86/superclaw) | OpenClaw エージェント専用レッドチームフレームワーク |
| [PyRIT](https://github.com/Azure/PyRIT) | Azure/Microsoft製 AIレッドチームツール |
| [Garak](https://github.com/leondz/garak) | LLM脆弱性スキャナー |

### 実行環境の注意事項

- 本番ネットワークや共有環境では実行しない
- 本プロジェクトの Azure VM（subnet-mgmt 内）での実行を推奨
- VM はインターネット非公開・Private Endpoint 経由のみ通信

---

## 6. トラブルシューティング

### `openclaw: command not found`

グローバルインストールのパスが通っていない可能性があります。

```bash
# npm グローバルパスの確認
npm config get prefix
# 出力されたパス/bin を PATH に追加
```

### 認証エラー（401 Unauthorized）

- `apiKey` が正しいか確認（Azure Portal → キーとエンドポイント）
- `baseUrl` が `https://<resource>.openai.azure.com` 形式か確認（末尾スラッシュ不要）

### モデルが見つからない（404 Not Found）

- `model` に指定した名前が Azure Portal の **デプロイ名** と一致しているか確認
- デプロイが「成功」ステータスであるか確認

### APIバージョン不一致

```bash
export AZURE_OPENAI_API_VERSION="2025-01-01-preview"
```

最新のサポートバージョンは [Azure OpenAI REST API リファレンス](https://learn.microsoft.com/en-us/azure/ai-services/openai/reference) を参照してください。

---

## 参考リンク

- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [OpenClaw 公式ドキュメント](https://docs.openclaw.ai)
- [SuperClaw（レッドチームフレームワーク）](https://github.com/Shashikant86/superclaw)
- [Azure OpenAI REST API リファレンス](https://learn.microsoft.com/en-us/azure/ai-services/openai/reference)
- [PyRIT（Microsoft AIレッドチームツール）](https://github.com/Azure/PyRIT)
