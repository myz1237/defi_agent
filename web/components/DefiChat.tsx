"use client";

// Shared chat component: consumes the backend SSE API.
// Anonymous session (localStorage); SIWE wallet connect is a placeholder for now.

import { useEffect, useRef, useState } from "react";
import { streamChat, streamResume, type SSEEvent } from "@/lib/api";

type ToolEvent = { kind: "call" | "result"; name: string; detail: string };
type Turn = {
  role: "user" | "assistant";
  text: string;
  tools: ToolEvent[];
};

function getSessionId(): string {
  if (typeof window === "undefined") return "anon";
  let sid = localStorage.getItem("defi_session_id");
  if (!sid) {
    sid = "web-" + Math.random().toString(36).slice(2, 14);
    localStorage.setItem("defi_session_id", sid);
  }
  return sid;
}

export default function DefiChat() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [interrupt, setInterrupt] = useState<string | null>(null);
  const sessionRef = useRef<string>("");
  const threadRef = useRef<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    sessionRef.current = getSessionId();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, interrupt]);

  // Drive a stream of SSE events into the latest assistant turn.
  async function consume(gen: AsyncGenerator<SSEEvent>) {
    // Start a fresh assistant turn that we mutate as events arrive.
    setTurns((t) => [...t, { role: "assistant", text: "", tools: [] }]);
    const patch = (fn: (turn: Turn) => Turn) =>
      setTurns((t) => {
        const next = [...t];
        next[next.length - 1] = fn(next[next.length - 1]);
        return next;
      });

    try {
      for await (const ev of gen) {
        if (ev.event === "start") {
          if (ev.data?.thread_id) threadRef.current = ev.data.thread_id;
        } else if (ev.event === "token") {
          patch((turn) => ({ ...turn, text: turn.text + (ev.data?.text ?? "") }));
        } else if (ev.event === "tool_call") {
          patch((turn) => ({
            ...turn,
            tools: [...turn.tools, { kind: "call", name: ev.data?.name, detail: JSON.stringify(ev.data?.args ?? {}) }],
          }));
        } else if (ev.event === "tool_result") {
          patch((turn) => ({
            ...turn,
            tools: [...turn.tools, { kind: "result", name: ev.data?.name, detail: ev.data?.content ?? "" }],
          }));
        } else if (ev.event === "interrupt") {
          setInterrupt(ev.data?.question ?? "More input needed");
        } else if (ev.event === "error") {
          patch((turn) => ({ ...turn, text: turn.text + `\n[error] ${ev.data?.error ?? ""}` }));
        }
      }
    } catch (e: any) {
      patch((turn) => ({ ...turn, text: turn.text + `\n[network error] ${e?.message ?? e}` }));
    }
  }

  async function send() {
    const message = input.trim();
    if (!message || busy) return;
    setInput("");
    setTurns((t) => [...t, { role: "user", text: message, tools: [] }]);
    setBusy(true);
    await consume(streamChat(sessionRef.current, message, threadRef.current));
    setBusy(false);
  }

  async function answerInterrupt() {
    const answer = input.trim();
    if (!answer || !threadRef.current) return;
    setInput("");
    setInterrupt(null);
    setTurns((t) => [...t, { role: "user", text: answer, tools: [] }]);
    setBusy(true);
    await consume(streamResume(sessionRef.current, threadRef.current, answer));
    setBusy(false);
  }

  return (
    <div className="chat">
      <header className="chat-header">
        <strong>DeFi Agent</strong>
        <span className="muted">read-only · ETH/BNB/ARB/BASE/OPT · LI.FI &amp; Morpho</span>
        <button className="wallet-btn" disabled title="Coming soon">
          Connect Wallet
        </button>
      </header>

      <div className="messages">
        {turns.length === 0 && (
          <div className="empty muted">
            Ask about a transaction hash or a wallet address. e.g. &quot;Is tx 0x7459… a cross-chain transfer?&quot;
          </div>
        )}
        {turns.map((turn, i) => (
          <div key={i} className={`turn ${turn.role}`}>
            {turn.tools.length > 0 && (
              <div className="tools">
                {turn.tools.map((tl, j) => (
                  <div key={j} className={`tool ${tl.kind}`}>
                    {tl.kind === "call" ? "→ " : "✓ "}
                    <code>{tl.name}</code>
                    {tl.kind === "call" && <span className="muted"> {tl.detail}</span>}
                  </div>
                ))}
              </div>
            )}
            {turn.text && <div className="bubble">{turn.text}</div>}
          </div>
        ))}
        {interrupt && <div className="interrupt">⚠ {interrupt}</div>}
        <div ref={bottomRef} />
      </div>

      <div className="composer">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (interrupt ? answerInterrupt() : send())}
          placeholder={interrupt ? "Type your answer…" : "Ask about a tx hash or wallet…"}
          disabled={busy}
        />
        <button onClick={() => (interrupt ? answerInterrupt() : send())} disabled={busy || !input.trim()}>
          {busy ? "…" : interrupt ? "Reply" : "Send"}
        </button>
      </div>
    </div>
  );
}
