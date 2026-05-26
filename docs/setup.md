# 開発環境セットアップガイド

フロントエンド（React）・バックエンド（FastAPI）の環境構築手順です。  
フロントエンド初心者向けに用語の説明を含めています。

---

## 目次

1. [前提知識：フロントエンド開発の仕組み](#1-前提知識フロントエンド開発の仕組み)
2. [フロントエンドのセットアップ](#2-フロントエンドのセットアップ)
3. [バックエンドのセットアップ](#3-バックエンドのセットアップ)
4. [両方を同時に起動する](#4-両方を同時に起動する)

---

## 1. 前提知識：フロントエンド開発の仕組み

### Node.js とは

ブラウザの外で JavaScript を動かすための実行環境です。

```
ブラウザ  → ユーザーが見る場所で JavaScript を動かす
Node.js  → 開発者のPCで JavaScript を動かす（ビルド・ツール実行など）
```

フロントエンド開発では「ブラウザに表示するコード」を書きますが、その**ビルド作業（コードを変換・まとめる処理）** は Node.js が担います。アプリの実行時には不要ですが、開発・ビルド時に必ず必要です。

インストール確認：

```bash
node --version   # v22.x.x 以上
npm --version    # 10.x.x 以上
```

### npm と package.json とは

**npm**（Node Package Manager）は Node.js に付属するパッケージ管理ツールです。`pip install`（Python）の JavaScript 版です。

**package.json** はプロジェクトの「設計図」ファイルです：

```json
{
  "scripts": {           // ← npm run dev などのコマンド定義
    "dev": "vite",
    "build": "vite build"
  },
  "dependencies": {      // ← 本番環境でも必要なライブラリ
    "react": "^18.3.1",
    "@assistant-ui/react": "^0.7.0"
  },
  "devDependencies": {   // ← 開発・ビルド時だけ必要なライブラリ
    "vite": "^5.4.2",
    "typescript": "^5.5.3"
  }
}
```

`npm install` を実行すると、`package.json` に書かれたすべてのライブラリが `node_modules/` にダウンロードされます。

> `node_modules/` は `.gitignore` で除外されています。クローン直後は必ず `npm install` が必要です。

### Vite とは

Vite（ヴィート）は**高速なビルドツール兼開発サーバー**です。役割は2つあります。

| モード | コマンド | 役割 |
|--------|----------|------|
| 開発サーバー | `npm run dev` | ファイル変更を即座にブラウザに反映（HMR） |
| 本番ビルド | `npm run build` | TypeScript・JSX をブラウザが読める JS にまとめる |

従来の webpack に比べて起動が数十倍速い点が特徴です。

**開発時の通信の流れ：**

```
ブラウザ
  ↓ http://localhost:5173  (Vite開発サーバー)
  ↓ /api/* は自動転送
バックエンド
  ↓ http://localhost:8000  (FastAPI)
```

この「`/api/*` を転送する」設定が `vite.config.ts` のプロキシ設定です。

### TypeScript とは

JavaScript に**型チェック**を加えた言語です。ファイル拡張子 `.ts` / `.tsx` を使います。

```typescript
// JavaScript: エラーが実行時まで分からない
function greet(name) { return "Hello " + name; }

// TypeScript: 引数の型を宣言 → 間違いをエディタが即座に指摘
function greet(name: string): string { return "Hello " + name; }
```

TypeScript はそのままブラウザでは動かないため、Vite がビルド時に JavaScript に変換します。

### React とは

UIを「コンポーネント（部品）」として組み立てるための JavaScript ライブラリです。

```
App.tsx
├── Sidebar.tsx       （左のスレッド一覧）
└── ChatArea.tsx      （右のチャット画面）
    └── Thread        （assistant-ui のコンポーネント）
```

`.tsx` は TypeScript + JSX（HTML っぽい記法を JS 内に書ける構文）です。

---

## 2. フロントエンドのセットアップ

### 2-1. 各設定ファイルの役割

```
frontend/
├── package.json          ← プロジェクト定義・依存ライブラリ一覧
├── vite.config.ts        ← Vite の設定（開発サーバー・ビルド設定）
├── tsconfig.json         ← TypeScript コンパイラの設定
├── tailwind.config.js    ← Tailwind CSS の設定
├── postcss.config.js     ← CSS 後処理の設定
├── index.html            ← アプリのエントリポイント HTML
└── src/
    ├── main.tsx          ← JS のエントリポイント（React をページに挿入）
    ├── index.css         ← グローバル CSS（Tailwind のベース読み込み）
    ├── App.tsx           ← アプリのルートコンポーネント
    ├── api.ts            ← バックエンド API の呼び出し関数
    ├── runtime.ts        ← assistant-ui のストリーミングアダプター
    └── components/
        ├── ChatArea.tsx      ← ストリーミングモードのチャット画面
        ├── NormalChatArea.tsx← 通常レスポンスモードのチャット画面
        └── Sidebar.tsx       ← スレッド一覧サイドバー
```

#### `vite.config.ts`

```typescript
export default defineConfig({
  plugins: [react()],   // JSX/TSX を処理するプラグイン
  server: {
    proxy: {
      "/api": "http://localhost:8000",    // /api/* をバックエンドに転送
      "/health": "http://localhost:8000",
    },
  },
});
```

開発時に `fetch("/api/chat")` を呼ぶと、Vite が自動的に `http://localhost:8000/api/chat` に転送します。これによりフロントとバックを別ポートで動かしながら、CORS（クロスオリジン制約）を回避しています。

#### `tsconfig.json`

TypeScript コンパイラの動作設定です。主要なオプション：

| 設定 | 意味 |
|------|------|
| `"target": "ES2020"` | 出力するJSのバージョン（古いブラウザ対応など） |
| `"strict": true` | 型チェックを厳しくする（推奨） |
| `"jsx": "react-jsx"` | JSX を React の記法で処理する |
| `"moduleResolution": "bundler"` | Vite 経由での import 解決方式 |
| `"noEmit": true` | TSはあくまで型チェック用。JS出力はViteに任せる |

#### `tailwind.config.js`

Tailwind CSS は「ユーティリティクラス」を提供するCSSフレームワークです（`className="flex bg-gray-100 text-sm"` のような書き方）。

```javascript
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    // assistant-ui が内部で使っている Tailwind クラスも対象にする（必須）
    "./node_modules/@assistant-ui/react-ui/dist/**/*.js",
  ],
  // ...
};
```

`content` に指定したファイルを Tailwind がスキャンし、使われているクラスだけを含む CSS を生成します。`@assistant-ui/react-ui` が内部で Tailwind クラスを使っているため、そのパスも含める必要があります（これを外すと assistant-ui のUIが崩れます）。

#### `postcss.config.js`

PostCSS は CSS の後処理ツールです。Tailwind 自体が PostCSS プラグインとして動作します。

```javascript
export default {
  plugins: {
    tailwindcss: {},   // Tailwind のクラスを CSS に展開
    autoprefixer: {},  // ベンダープレフィックス（-webkit- など）を自動付与
  },
};
```

通常、この設定を変更する必要はありません。

#### `index.html`

```html
<div id="root"></div>
<script type="module" src="/src/main.tsx"></script>
```

React アプリは `<div id="root">` の中にすべてのUIを描画します。`main.tsx` がその起点です。

---

### 2-2. assistant-ui の構成と推奨セットアップ

assistant-ui は React 向けのチャットUIライブラリです。このプロジェクトでの採用理由は、ストリーミングレスポンスのUI実装（文字が流れてくる表示）が簡単に実現できるためです。

**パッケージ構成：**

| パッケージ | 役割 |
|------------|------|
| `@assistant-ui/react` | コアロジック（ランタイム・フック） |
| `@assistant-ui/react-ui` | 既製UIコンポーネント（`<Thread />` など） |

**推奨セットアップの流れ（現在のコードはこの構成です）：**

```
1. ChatModelAdapter を実装する（LLMとの通信ロジック）
         ↓
2. useLocalRuntime() でランタイムを生成
         ↓
3. AssistantRuntimeProvider でコンポーネントをラップ
         ↓
4. <Thread /> でチャットUIを表示
```

**`runtime.ts` — ChatModelAdapter の実装：**

```typescript
// assistant-ui が送信ボタンを押したときに呼ぶ関数
export function createAdapter(opts): ChatModelAdapter {
  return {
    async *run({ messages, abortSignal }) {
      // ① ファイルをアップロード
      // ② バックエンドの SSE エンドポイントを呼ぶ
      // ③ テキストチャンクを yield → Thread に随時表示される
      yield { content: [{ type: "text", text: "..." }] };
    },
  };
}
```

`run` が `async *`（非同期ジェネレーター）であることが重要です。`yield` するたびにUIがリアルタイム更新されます。

**`ChatArea.tsx` — ランタイムとUIの接続：**

```typescript
const adapter = useMemo(() => createAdapter({ ... }), []);
const runtime = useLocalRuntime(adapter, {
  initialMessages: threadMessages,  // スレッド切替時の履歴復元
});

return (
  <AssistantRuntimeProvider runtime={runtime}>
    <Thread />   {/* これだけでチャットUI全体が表示される */}
  </AssistantRuntimeProvider>
);
```

> **現在のコードは assistant-ui の推奨構成に沿っています。変更不要です。**

---

### 2-3. インストールと起動

```bash
cd frontend

# 依存ライブラリのインストール（初回・package.json 変更時に実行）
npm install

# 開発サーバー起動
npm run dev
```

ブラウザで `http://localhost:5173` を開くとアプリが表示されます。

**ファイルを変更すると自動でブラウザに反映されます（HMR = Hot Module Replacement）。** サーバーの再起動は不要です。

**本番用ビルド（Azure App Service へのデプロイ時）：**

```bash
npm run build
# dist/ フォルダにビルド済みファイルが生成される
```

---

### 2-4. よくあるトラブル

| 症状 | 原因 | 対処 |
|------|------|------|
| `Cannot find module '...'` | `npm install` をしていない | `npm install` を実行 |
| バックエンドに繋がらない（502） | FastAPI が起動していない | バックエンドを先に起動する |
| UIが崩れる（assistant-ui） | tailwind.config.js の content に assistant-ui のパスがない | `tailwind.config.js` の `content` を確認 |
| 変更が反映されない | ブラウザキャッシュ | `Ctrl+Shift+R` で強制リロード |

---

## 3. バックエンドのセットアップ

### 3-1. 仮想環境とは

Python は**仮想環境（venv）** でプロジェクトごとに依存ライブラリを分離します。Node.js の `node_modules/` に相当する仕組みです。

```
システム全体の Python
└── venv/ （このプロジェクト専用の Python 環境）
    └── lib/
        ├── fastapi/
        └── uvicorn/
```

### 3-2. インストールと起動

```bash
cd backend

# 仮想環境の作成（初回のみ）
python -m venv venv

# 仮想環境の有効化
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# Windows (コマンドプロンプト)
.\venv\Scripts\activate.bat
# Linux / macOS
source venv/bin/activate

# 依存ライブラリのインストール
pip install -r requirements.txt

# 開発サーバー起動
uvicorn app.main:app --reload --port 8000
```

`--reload` オプションを付けると、ファイル変更時に自動でサーバーが再起動します。

### 3-3. 各ファイルの役割

```
backend/
├── requirements.txt       ← pip でインストールするライブラリ一覧
└── app/
    ├── main.py            ← FastAPI アプリの起点・CORS設定
    ├── schemas.py         ← リクエスト/レスポンスの型定義（Pydantic）
    ├── storage.py         ← インメモリのスレッド/メッセージ管理（再起動でリセット）
    ├── llm.py             ← LLM接続層（現在はダミーのオウム返し実装）
    └── routers/
        ├── chat.py        ← /api/chat（SSE）, /api/chat/simple（JSON）
        ├── threads.py     ← /api/threads（一覧・削除）
        └── files.py       ← /api/upload（ファイルアップロード）
```

### 3-4. API 確認（Swagger UI）

FastAPI は自動でAPIドキュメントを生成します。

```
http://localhost:8000/docs
```

ブラウザで上記にアクセスすると、全APIをブラウザ上でテストできます。

### 3-5. よくあるトラブル

| 症状 | 原因 | 対処 |
|------|------|------|
| `ModuleNotFoundError` | 仮想環境が有効でない、または `pip install` 未実行 | 仮想環境を activate してから `pip install -r requirements.txt` |
| Port 8000 already in use | 別のプロセスが使用中 | `lsof -i:8000` でプロセスを確認して終了 |
| `uvicorn: command not found` | 仮想環境が有効でない | `source venv/bin/activate` を実行 |

---

## 4. 両方を同時に起動する

ターミナルを2つ開いて、それぞれで起動します。

**ターミナル1（バックエンド）：**

```bash
cd backend
source venv/bin/activate   # Windows: .\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

**ターミナル2（フロントエンド）：**

```bash
cd frontend
npm run dev
```

`http://localhost:5173` をブラウザで開いてチャットが動作すれば成功です。

---

## 参考：Azure デプロイ時の違い

| 項目 | ローカル開発 | Azure App Service |
|------|------------|-------------------|
| フロントのURL | `localhost:5173` | `https://<app>.azurewebsites.net` |
| APIの転送 | Vite プロキシ（自動） | App Service のルーティング設定 |
| ビルド | 不要（開発サーバーが処理） | `npm run build` → `dist/` を配置 |
| バックエンドURL | `localhost:8000` | Private Endpoint 経由の内部 URL |
