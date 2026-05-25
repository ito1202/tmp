export interface ApiMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  file_ids: string[];
  created_at: string;
}

export interface ApiThread {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface UploadResult {
  file_id: string;
  filename: string;
  content_type: string;
}

export async function fetchThreads(): Promise<ApiThread[]> {
  const res = await fetch("/api/threads");
  if (!res.ok) throw new Error("Failed to fetch threads");
  return res.json();
}

export async function fetchMessages(threadId: string): Promise<ApiMessage[]> {
  const res = await fetch(`/api/threads/${threadId}/messages`);
  if (!res.ok) throw new Error("Failed to fetch messages");
  return res.json();
}

export async function deleteThread(threadId: string): Promise<void> {
  await fetch(`/api/threads/${threadId}`, { method: "DELETE" });
}

export async function uploadFile(file: File): Promise<UploadResult> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch("/api/upload", { method: "POST", body: fd });
  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}

export async function chatSimple(
  messages: { role: string; content: string; file_ids: string[] }[],
  threadId: string | null
): Promise<{ thread_id: string; content: string }> {
  const res = await fetch("/api/chat/simple", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, thread_id: threadId }),
  });
  if (!res.ok) throw new Error("Chat request failed");
  return res.json();
}

export async function* streamChat(
  messages: { role: string; content: string; file_ids: string[] }[],
  threadId: string | null,
  signal: AbortSignal
): AsyncGenerator<{ type: string; [key: string]: string }> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, thread_id: threadId }),
    signal,
  });

  if (!res.ok || !res.body) throw new Error("Chat request failed");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      try {
        yield JSON.parse(line.slice(6));
      } catch {
        // skip malformed lines
      }
    }
  }
}
