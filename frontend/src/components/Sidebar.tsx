import { useEffect, useState, useCallback } from "react";
import { fetchThreads, deleteThread, type ApiThread } from "../api";

interface Props {
  activeThreadId: string | null;
  onSelectThread: (threadId: string) => void;
  onNewChat: () => void;
  refreshSignal: number; // 増えるたびに一覧を再取得
}

export function Sidebar({
  activeThreadId,
  onSelectThread,
  onNewChat,
  refreshSignal,
}: Props) {
  const [threads, setThreads] = useState<ApiThread[]>([]);

  const load = useCallback(async () => {
    try {
      setThreads(await fetchThreads());
    } catch {
      // サーバー未起動時は無視
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshSignal]);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    await deleteThread(id);
    setThreads((prev) => prev.filter((t) => t.id !== id));
    if (activeThreadId === id) onNewChat();
  };

  return (
    <aside className="w-60 shrink-0 flex flex-col bg-gray-900 text-white h-full">
      <div className="p-3 border-b border-gray-700">
        <button
          onClick={onNewChat}
          className="w-full py-2 px-3 rounded-lg bg-gray-700 hover:bg-gray-600 text-sm text-left"
        >
          ＋ 新しいチャット
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto p-2 space-y-1">
        {threads.length === 0 && (
          <p className="text-xs text-gray-500 px-2 pt-2">履歴なし</p>
        )}
        {threads.map((t) => (
          <div
            key={t.id}
            onClick={() => onSelectThread(t.id)}
            className={`group flex items-center justify-between rounded-lg px-3 py-2 text-sm cursor-pointer ${
              t.id === activeThreadId
                ? "bg-gray-600"
                : "hover:bg-gray-700"
            }`}
          >
            <span className="truncate flex-1">{t.title}</span>
            <button
              onClick={(e) => handleDelete(e, t.id)}
              className="ml-1 hidden group-hover:block text-gray-400 hover:text-red-400 text-xs"
              title="削除"
            >
              ✕
            </button>
          </div>
        ))}
      </nav>
    </aside>
  );
}
