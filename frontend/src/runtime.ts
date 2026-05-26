import { type ChatModelAdapter } from "@assistant-ui/react";
import { uploadFile, streamChat } from "./api";

/**
 * assistant-ui の ChatModelAdapter 実装。
 * - pendingFiles: 送信前にユーザーが選択したファイル（外部 ref 経由で受け取る）
 * - threadId: 現在のスレッドID（外部 ref 経由で読み書き）
 */
export function createAdapter(opts: {
  getThreadId: () => string | null;
  setThreadId: (id: string) => void;
  getPendingFiles: () => File[];
  clearPendingFiles: () => void;
}): ChatModelAdapter {
  return {
    async *run({ messages, abortSignal }) {
      // ① ファイルをアップロード
      const files = opts.getPendingFiles();
      const fileIds: string[] = [];
      for (const file of files) {
        const result = await uploadFile(file);
        fileIds.push(result.file_id);
      }
      opts.clearPendingFiles();

      // ② messages を API 形式に変換（最後のユーザーメッセージにファイルIDを付与）
      const apiMessages = messages.map((m, i) => ({
        role: m.role,
        content: m.content
          .filter((c) => c.type === "text")
          .map((c) => (c as { type: "text"; text: string }).text)
          .join(""),
        file_ids: i === messages.length - 1 ? fileIds : [],
      }));

      // ③ SSE ストリームを受信してテキストを yield
      for await (const event of streamChat(
        apiMessages,
        opts.getThreadId(),
        abortSignal
      )) {
        if (event.type === "thread_id") {
          opts.setThreadId(event.thread_id);
        } else if (event.type === "text") {
          yield { content: [{ type: "text", text: event.content }] };
        }
      }
    },
  };
}
