"use client";

// Controller/host: owns the message thread + wallet, maps backend SSE -> ChatMessage[],
// and renders the presentational <DeFiAgentChat /> (card-based UI).

import { useEffect, useRef, useState } from "react";
import { DeFiAgentChat, mapLifiStatus } from "@/chat-ui";
import type { ChatMessage, MorphoView } from "@/chat-ui/types";
import { streamChat, streamResume, type SSEEvent } from "@/lib/api";
import { connectWallet, type WalletSession } from "@/lib/wallet";

const uid = () => (typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`);

function getSessionId(): string {
  let sid = localStorage.getItem("defi_session_id");
  if (!sid) {
    sid = "web-" + Math.random().toString(36).slice(2, 14);
    localStorage.setItem("defi_session_id", sid);
  }
  return sid;
}

const short = (a: string) => `${a.slice(0, 6)}…${a.slice(-4)}`;

const SUGGESTIONS = [
  {
    label: "Is tx 0x7459… cross-chain?",
    query: "Is tx 0x7459b8d8fa53ca8d9d3fbcb835b28cedb12f0fb34bdd4dcb5579a8ebb87a1abd a completed cross-chain transfer?",
  },
  {
    label: "Morpho positions (0x7b52…)",
    query: "Show Morpho positions for 0x7b524b0308a776a7d4E65A2Db73bB37881818748",
  },
  { label: "My Morpho positions", query: "Show my Morpho positions" },
  { label: "How does Morpho liquidation work?", query: "How does Morpho liquidation work?" },
];

export default function DefiChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [thinking, setThinking] = useState(false);
  const [awaitingResume, setAwaitingResume] = useState(false);
  const [wallet, setWallet] = useState<WalletSession | null>(null);

  const sessionRef = useRef<string>("");
  const threadRef = useRef<string | null>(null);
  const tokenRef = useRef<string | null>(null);

  useEffect(() => {
    sessionRef.current = getSessionId();
    const saved = localStorage.getItem("defi_wallet");
    if (saved) {
      const w = JSON.parse(saved) as WalletSession;
      setWallet(w);
      tokenRef.current = w.token;
    }
  }, []);

  const append = (m: ChatMessage) => setMessages((prev) => [...prev, m]);

  async function consume(gen: AsyncGenerator<SSEEvent>) {
    let agentTextId: string | null = null; // local: avoids strict-mode ref pitfalls
    try {
      for await (const ev of gen) {
        if (ev.event === "start") {
          if (ev.data?.thread_id) threadRef.current = ev.data.thread_id;
        } else if (ev.event === "token") {
          const delta: string = ev.data?.text ?? "";
          if (!delta) continue;
          if (!agentTextId) {
            const id = (agentTextId = uid());
            append({ id, role: "agent", text: delta });
          } else {
            const id = agentTextId;
            setMessages((prev) =>
              prev.map((x) => (x.id === id && "text" in x ? { ...x, text: x.text + delta } : x)),
            );
          }
        } else if (ev.event === "card") {
          if (ev.data?.kind === "lifi") {
            append({ id: uid(), role: "agent", card: { kind: "lifi", data: mapLifiStatus(ev.data.raw) } });
          } else if (ev.data?.kind === "morpho") {
            append({ id: uid(), role: "agent", card: { kind: "morpho", data: ev.data.data as MorphoView } });
          }
        } else if (ev.event === "interrupt") {
          append({ id: uid(), role: "agent", text: ev.data?.question ?? "More input needed." });
          setAwaitingResume(true);
        } else if (ev.event === "error") {
          append({ id: uid(), role: "agent", text: `[error] ${ev.data?.error ?? ""}` });
        }
      }
    } catch (e: any) {
      append({ id: uid(), role: "agent", text: `[network error] ${e?.message ?? e}` });
    }
  }

  async function onSend(text: string) {
    if (thinking) return;
    append({ id: uid(), role: "user", text });
    setThinking(true);
    const resuming = awaitingResume;
    if (resuming) setAwaitingResume(false);
    const gen = resuming
      ? streamResume(sessionRef.current, threadRef.current!, text, tokenRef.current)
      : streamChat(sessionRef.current, text, threadRef.current, tokenRef.current);
    await consume(gen);
    setThinking(false);
  }

  async function onConnectWallet() {
    if (wallet) {
      setWallet(null);
      tokenRef.current = null;
      threadRef.current = null; // identity changed -> fresh thread
      localStorage.removeItem("defi_wallet");
      return;
    }
    try {
      const w = await connectWallet();
      setWallet(w);
      tokenRef.current = w.token;
      threadRef.current = null;
      localStorage.setItem("defi_wallet", JSON.stringify(w));
    } catch (e: any) {
      append({ id: uid(), role: "agent", text: `[wallet] ${e?.message ?? "connect failed"}` });
    }
  }

  return (
    <DeFiAgentChat
      messages={messages}
      thinking={thinking}
      onSend={onSend}
      onConnectWallet={onConnectWallet}
      walletLabel={wallet ? `${short(wallet.address)} · DISCONNECT` : "CONNECT WALLET"}
      placeholder={awaitingResume ? "type your answer…" : "ask about a tx hash or wallet…"}
      suggestions={SUGGESTIONS}
    />
  );
}
