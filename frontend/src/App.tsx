import { useState, useCallback } from "react";
import { Sidebar } from "./components/Sidebar";
import { ChatArea } from "./components/ChatArea";
import { NormalChatArea } from "./components/NormalChatArea";
import { fetchMessages, type ApiMessage } from "./api";

type Mode = "stream" | "normal";

interface ActiveThread {
  id: string;
  messages: ApiMessage[];
}

export default function App() {
  const [mode, setMode] = useState<Mode>("stream");
  // null = 新規チャット
  const [activeThread, setActiveThread] = useState<ActiveThread | null>(null);
  // Sidebar の一覧更新トリガー
  const [refreshSignal, setRefreshSignal] = useState(0);

  const refreshSidebar = () => setRefreshSignal((n) => n + 1);

  const handleSelectThread = useCallback(async (threadId: string) => {
    const messages = await fetchMessages(threadId);
    setActiveThread({ id: threadId, messages });
  }, []);

  const handleNewChat = useCallback(() => {
    setActiveThread(null);
  }, []);

  const handleThreadIdChange = useCallback((id: string) => {
    // バックエンドでスレッドが作成・確定したらサイドバーを更新
    setActiveThread((prev) => (prev ? prev : { id, messages: [] }));
    refreshSidebar();
  }, []);

  // key を変えることで ChatArea を再マウント → スレッド切替・initialMessages の再適用
  const chatKey = activeThread?.id ?? "new";

  return (
    <div className="flex h-screen bg-white">
      <Sidebar
        activeThreadId={activeThread?.id ?? null}
        onSelectThread={handleSelectThread}
        onNewChat={handleNewChat}
        refreshSignal={refreshSignal}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* モード切替タブ */}
        <div className="flex border-b border-gray-200 bg-white shrink-0">
          {(["stream", "normal"] as Mode[]).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                mode === m
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {m === "stream" ? "ストリーミング" : "通常レスポンス"}
            </button>
          ))}
        </div>

        {/* チャットエリア */}
        <div className="flex-1 overflow-hidden">
          {mode === "stream" ? (
            <ChatArea
              key={`stream-${chatKey}`}
              initialThreadId={activeThread?.id ?? null}
              initialMessages={activeThread?.messages ?? []}
              onThreadIdChange={handleThreadIdChange}
            />
          ) : (
            <NormalChatArea
              key={`normal-${chatKey}`}
              initialThreadId={activeThread?.id ?? null}
              initialMessages={activeThread?.messages ?? []}
              onThreadIdChange={handleThreadIdChange}
            />
          )}
        </div>
      </div>
    </div>
  );
}
