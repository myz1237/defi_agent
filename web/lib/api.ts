// 消费后端 SSE:fetch + ReadableStream(EventSource 不便带 POST/头)。

export type SSEEvent = { event: string; data: any };

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

async function* parseSSE(resp: Response): AsyncGenerator<SSEEvent> {
  const reader = resp.body!.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    // Normalize CRLF -> LF: sse-starlette separates events with \r\n.
    buf += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
    let idx: number;
    while ((idx = buf.indexOf("\n\n")) >= 0) {
      const raw = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      let event = "message";
      let dataStr = "";
      for (const line of raw.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) dataStr += line.slice(5).trim();
        // 以 ":" 开头的是注释/心跳(sse-starlette ping),忽略
      }
      if (!dataStr) continue;
      let data: any = dataStr;
      try {
        data = JSON.parse(dataStr);
      } catch {
        // 保留原始字符串
      }
      yield { event, data };
    }
  }
}

async function* stream(
  path: string,
  sessionId: string,
  body: unknown,
  token?: string | null,
): AsyncGenerator<SSEEvent> {
  const headers: Record<string, string> = { "Content-Type": "application/json", "X-Session-Id": sessionId };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const resp = await fetch(API_BASE + path, { method: "POST", headers, body: JSON.stringify(body) });
  if (!resp.ok || !resp.body) throw new Error(`HTTP ${resp.status}`);
  yield* parseSSE(resp);
}

export function streamChat(sessionId: string, message: string, threadId: string | null, token?: string | null) {
  return stream("/v1/chat", sessionId, { message, thread_id: threadId }, token);
}

export function streamResume(sessionId: string, threadId: string, resume: string, token?: string | null) {
  return stream("/v1/chat/resume", sessionId, { thread_id: threadId, resume }, token);
}
