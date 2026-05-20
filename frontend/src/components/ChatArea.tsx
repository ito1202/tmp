import { useRef, useState, useMemo } from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ThreadMessageLike,
} from "@assistant-ui/react";
import { Thread } from "@assistant-ui/react-ui";
import { createAdapter } from "../runtime";
import { type ApiMessage } from "../api";

interface Props {
  initialThreadId: string | null;
  initialMessages: ApiMessage[];
  onThreadIdChange: (id: string) => void;
}

/**
 * key={threadId} で親から再マウントされることでスレッド切替を実現する。
 * initialMessages は useState の初期値として渡すため、再マウント時に確実に反映される。
 */
export function ChatArea({
  initialThreadId,
  initialMessages,
  onThreadIdChange,
}: Props) {
  const threadIdRef = useRef<string | null>(initialThreadId);
  const pendingFilesRef = useRef<File[]>([]);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);

  const updateFiles = (files: File[]) => {
    pendingFilesRef.current = files;
    setPendingFiles([...files]);
  };

  const adapter = useMemo(
    () =>
      createAdapter({
        getThreadId: () => threadIdRef.current,
        setThreadId: (id) => {
          threadIdRef.current = id;
          onThreadIdChange(id);
        },
        getPendingFiles: () => pendingFilesRef.current,
        clearPendingFiles: () => updateFiles([]),
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const threadMessages: ThreadMessageLike[] = initialMessages.map((m) => ({
    role: m.role as "user" | "assistant",
    content: [{ type: "text" as const, text: m.content }],
  }));

  const runtime = useLocalRuntime(adapter, {
    initialMessages: threadMessages,
  });

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    updateFiles([...pendingFilesRef.current, ...Array.from(e.target.files)]);
    e.target.value = "";
  };

  const removeFile = (index: number) => {
    updateFiles(pendingFilesRef.current.filter((_, i) => i !== index));
  };

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="flex flex-col h-full">
        {/* ファイル添付エリア */}
        <div className="flex items-center gap-2 px-4 py-2 bg-gray-50 border-b border-gray-200 min-h-[44px]">
          <label className="flex items-center gap-1 cursor-pointer text-sm text-gray-500 hover:text-gray-800">
            <span>📎</span>
            <span>ファイルを添付</span>
            <input
              type="file"
              multiple
              className="hidden"
              onChange={handleFileInput}
            />
          </label>
          {pendingFiles.map((f, i) => (
            <span
              key={i}
              className="flex items-center gap-1 bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full"
            >
              {f.name}
              <button
                onClick={() => removeFile(i)}
                className="hover:text-red-600 font-bold"
              >
                ×
              </button>
            </span>
          ))}
        </div>

        {/* チャット本体 */}
        <div className="flex-1 overflow-hidden">
          <Thread />
        </div>
      </div>
    </AssistantRuntimeProvider>
  );
}
