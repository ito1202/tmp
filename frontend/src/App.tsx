import { useState, useCallback } from "react";
import { Sidebar } from "./components/Sidebar";
import { ChatArea } from "./components/ChatArea";
import { fetchMessages, type ApiMessage } from "./api";

interface ActiveThread {
  id: string;
  messages: ApiMessage[];
}

export default function App() {
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
      <main className="flex-1 overflow-hidden">
        <ChatArea
          key={chatKey}
          initialThreadId={activeThread?.id ?? null}
          initialMessages={activeThread?.messages ?? []}
          onThreadIdChange={handleThreadIdChange}
        />
      </main>
    </div>
  );
}
