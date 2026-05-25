import { useRef, useState } from "react";
import { chatSimple, uploadFile, type ApiMessage } from "../api";

interface Props {
  initialThreadId: string | null;
  initialMessages: ApiMessage[];
  onThreadIdChange: (id: string) => void;
}

export function NormalChatArea({
  initialThreadId,
  initialMessages,
  onThreadIdChange,
}: Props) {
  const [messages, setMessages] = useState<ApiMessage[]>(initialMessages);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const threadIdRef = useRef<string | null>(initialThreadId);
  const bottomRef = useRef<HTMLDivElement>(null);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    setPendingFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
    e.target.value = "";
  };

  const handleSend = async () => {
    if (!input.trim() && pendingFiles.length === 0) return;

    const fileIds: string[] = [];
    for (const file of pendingFiles) {
      const result = await uploadFile(file);
      fileIds.push(result.file_id);
    }
    setPendingFiles([]);

    const userMsg: ApiMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: input,
      file_ids: fileIds,
      created_at: new Date().toISOString(),
    };
    const next = [...messages, userMsg];
    setMessages(next);
    setInput("");
    setLoading(true);

    try {
      const res = await chatSimple(
        next.map((m) => ({ role: m.role, content: m.content, file_ids: m.file_ids })),
        threadIdRef.current
      );
      threadIdRef.current = res.thread_id;
      onThreadIdChange(res.thread_id);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: res.content,
          file_ids: [],
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* ファイル添付エリア */}
      <div className="flex items-center gap-2 px-4 py-2 bg-gray-50 border-b border-gray-200 min-h-[44px]">
        <label className="flex items-center gap-1 cursor-pointer text-sm text-gray-500 hover:text-gray-800">
          <span>📎</span>
          <span>ファイルを添付</span>
          <input type="file" multiple className="hidden" onChange={handleFileInput} />
        </label>
        {pendingFiles.map((f, i) => (
          <span
            key={i}
            className="flex items-center gap-1 bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full"
          >
            {f.name}
            <button
              onClick={() => setPendingFiles((prev) => prev.filter((_, j) => j !== i))}
              className="hover:text-red-600 font-bold"
            >
              ×
            </button>
          </span>
        ))}
      </div>

      {/* メッセージ一覧 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <p className="text-center text-gray-400 text-sm mt-8">メッセージを送信してください</p>
        )}
        {messages.map((m) => (
          <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[70%] px-4 py-2 rounded-2xl text-sm whitespace-pre-wrap ${
                m.role === "user"
                  ? "bg-blue-500 text-white rounded-br-sm"
                  : "bg-gray-100 text-gray-800 rounded-bl-sm"
              }`}
            >
              {m.content}
              {m.file_ids.length > 0 && (
                <p className="text-xs opacity-70 mt-1">📎 {m.file_ids.length} 件</p>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-500 text-sm px-4 py-2 rounded-2xl rounded-bl-sm">
              考え中...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* 入力エリア */}
      <div className="border-t border-gray-200 p-4 flex gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="メッセージを入力（Shift+Enter で改行）"
          rows={2}
          className="flex-1 border border-gray-300 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-400"
          disabled={loading}
        />
        <button
          onClick={handleSend}
          disabled={loading || (!input.trim() && pendingFiles.length === 0)}
          className="px-4 py-2 bg-blue-500 text-white rounded-xl text-sm font-medium disabled:opacity-40 hover:bg-blue-600"
        >
          送信
        </button>
      </div>
    </div>
  );
}
