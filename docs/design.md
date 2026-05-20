# AI Chat アプリ 基本設計書

## 1. システム概要

VPN閉域網内で動作するAIチャットWebアプリ。  
ブラウザからファイルを添付してAIと会話でき、会話はスレッド単位で保持する。  
バックエンドはAzure AI Foundry（エージェント）と接続する設計だが、現フェーズはダミー実装（オウム返し）。

---

## 2. 画面構成

```
┌─────────────┬────────────────────────────────────┐
│  Sidebar    │  Chat Area                         │
│             │                                    │
│ + 新規チャット│  [メッセージ一覧]                    │
│             │                                    │
│ スレッド1   │  📎 添付ファイルエリア                │
│ スレッド2   │  ┌──────────────────────────────┐  │
│ ...         │  │ メッセージ入力         [送信] │  │
│             │  └──────────────────────────────┘  │
└─────────────┴────────────────────────────────────┘
```

---

## 3. コンポーネント構成

### Frontend

| コンポーネント | 役割 |
|-------------|------|
| `App` | ルートレイアウト。アクティブスレッドの状態管理 |
| `Sidebar` | スレッド一覧・新規作成・削除 |
| `ChatArea` | チャット本体。`key={threadId}` でスレッド切替時に再マウント |

`ChatArea` は `useLocalRuntime`（@assistant-ui/react）でバックエンドと接続し、  
`Thread`（@assistant-ui/react-ui）でメッセージ表示・入力UIを提供する。

### Backend

| モジュール | 役割 |
|----------|------|
| `routers/chat.py` | チャット送受信（SSE streaming） |
| `routers/files.py` | ファイルアップロード |
| `routers/threads.py` | スレッドCRUD |
| `llm.py` | LLMサービス抽象クラス + DummyImpl |
| `storage.py` | インメモリストア（threads・files） |

---

## 4. API仕様

| Method | Path | 概要 |
|--------|------|------|
| POST | `/api/chat` | チャット（SSE streaming） |
| POST | `/api/upload` | ファイルアップロード |
| GET | `/api/threads` | スレッド一覧 |
| GET | `/api/threads/{id}/messages` | スレッドのメッセージ取得 |
| DELETE | `/api/threads/{id}` | スレッド削除 |
| GET | `/health` | ヘルスチェック |

### POST /api/chat

Request:
```json
{
  "messages": [
    { "role": "user", "content": "こんにちは", "file_ids": ["uuid-xxx"] }
  ],
  "thread_id": null
}
```

Response（`text/event-stream`）:
```
data: {"type": "thread_id", "thread_id": "uuid-yyy"}
data: {"type": "text", "content": "こ"}
data: {"type": "text", "content": "ん"}
data: {"type": "done"}
```

### POST /api/upload

Request: `multipart/form-data` (field: `file`)  
Response:
```json
{ "file_id": "uuid-xxx", "filename": "doc.pdf", "content_type": "application/pdf" }
```

---

## 5. データモデル

### Thread

| フィールド | 型 | 説明 |
|---------|---|------|
| id | string | UUID |
| title | string | 最初のユーザー発言（30文字で切る） |
| created_at | datetime | 作成日時 |
| updated_at | datetime | 最終更新日時 |

### Message

| フィールド | 型 | 説明 |
|---------|---|------|
| id | string | UUID |
| role | "user" \| "assistant" | 送信者 |
| content | string | テキスト本文 |
| file_ids | string[] | 添付ファイルIDリスト |
| created_at | datetime | 作成日時 |

### File（インメモリ）

| フィールド | 型 | 説明 |
|---------|---|------|
| file_id | string | UUID |
| filename | string | 元ファイル名 |
| content_type | string | MIMEタイプ |
| content | bytes | ファイル内容（Foundry連携時に使用） |

---

## 6. 技術スタック

| レイヤー | 採用技術 |
|---------|---------|
| Frontend | React 18 / TypeScript / Vite |
| Chat UI | @assistant-ui/react・@assistant-ui/react-ui |
| Styling | Tailwind CSS |
| Backend | Python 3.11+ / FastAPI / uvicorn |
| LLM | `DummyLLMService`（Foundry接続時に差し替え） |
| Storage | インメモリ（サーバー再起動でリセット） |

---

## 7. ディレクトリ構成

```
frontend/
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── index.html
└── src/
    ├── main.tsx
    ├── App.tsx              # ルート・スレッド状態管理
    ├── api.ts               # fetch ラッパー
    ├── runtime.ts           # ChatModelAdapter（FastAPI接続）
    └── components/
        ├── Sidebar.tsx      # スレッド一覧
        └── ChatArea.tsx     # assistant-ui プロバイダー + Thread

backend/
├── requirements.txt
└── app/
    ├── main.py              # FastAPI + CORS
    ├── schemas.py           # Pydantic モデル
    ├── storage.py           # インメモリストア
    ├── llm.py               # LLMサービス（Dummy / Foundry）
    └── routers/
        ├── chat.py
        ├── files.py
        └── threads.py
```

---

## 8. Foundry 接続時の変更点

`backend/app/llm.py` の最終行のみ変更する。

```python
# 現在（ダミー）
llm_service: BaseLLMService = DummyLLMService()

# Foundry接続後
llm_service: BaseLLMService = FoundryLLMService(
    endpoint=os.environ["FOUNDRY_ENDPOINT"],
    agent_id=os.environ["FOUNDRY_AGENT_ID"],
)
```

`stream(messages, file_ids)` のインターフェースは変わらない。
