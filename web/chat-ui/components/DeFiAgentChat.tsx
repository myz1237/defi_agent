'use client';
import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { colors, font } from '../theme';
import type { ChatMessage, Suggestion } from '../types';
import { ChatMessageView } from './ChatMessageView';

export const defaultSuggestions: Suggestion[] = [
  { label: 'Is tx 0x5e9b… complete?', query: 'Is tx 0x5e9b…2327c a completed transfer?' },
  { label: 'My Morpho positions', query: 'Show my Morpho positions' },
  { label: 'Token balances', query: 'Show my token balances' },
];

export interface DeFiAgentChatProps {
  /** Full message thread (controlled — owned by your agent/host state). */
  messages: ChatMessage[];
  /** Called when the user submits text (Enter, Send, or a suggestion chip). */
  onSend: (text: string) => void;
  /** Show the typing indicator while your agent is working. */
  thinking?: boolean;
  suggestions?: Suggestion[];
  placeholder?: string;
  header?: { title: string; subtitle: string };
  walletLabel?: string;
  onConnectWallet?: () => void;
  /** Fixed height; defaults to filling the parent (100%). */
  height?: number | string;
}

let stylesInjected = false;
function useChatStyles() {
  useEffect(() => {
    if (stylesInjected || typeof document === 'undefined') return;
    stylesInjected = true;
    const el = document.createElement('style');
    el.id = 'defi-agent-chat-styles';
    el.textContent = `
@keyframes dac-blink{0%,80%,100%{opacity:.22}40%{opacity:1}}
@keyframes dac-msgin{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.dac-scroll::-webkit-scrollbar{width:9px;height:9px}
.dac-scroll::-webkit-scrollbar-thumb{background:rgba(255,255,255,.1);border-radius:9px}
.dac-scroll::-webkit-scrollbar-track{background:transparent}
.dac-input::placeholder{color:${colors.faint}}
`;
    document.head.appendChild(el);
  }, []);
}

const Dot: React.FC<{ delay: number }> = ({ delay }) => (
  <span
    style={{
      width: 6,
      height: 6,
      borderRadius: '50%',
      background: colors.accent,
      animation: `dac-blink 1.2s ${delay}s infinite`,
    }}
  />
);

export const DeFiAgentChat: React.FC<DeFiAgentChatProps> = ({
  messages,
  onSend,
  thinking = false,
  suggestions = defaultSuggestions,
  placeholder = 'ask about a tx hash or wallet…',
  header = { title: 'DeFi Agent', subtitle: 'READ-ONLY · ETH/BNB/ARB/BASE/OPT · LI.FI & MORPHO' },
  walletLabel = 'CONNECT WALLET',
  onConnectWallet,
  height = '100%',
}) => {
  useChatStyles();
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, thinking]);

  const submit = () => {
    const v = input.trim();
    if (!v) return;
    setInput('');
    onSend(v);
  };

  const empty = messages.length === 0 && !thinking;

  return (
    <div
      style={{
        height,
        display: 'flex',
        flexDirection: 'column',
        background: colors.bg,
        color: colors.text,
        fontFamily: font.sans,
      }}
    >
      {/* header */}
      <div
        style={{
          flex: 'none',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 20px',
          borderBottom: `1px solid ${colors.line}`,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 11 }}>
          <span
            style={{
              width: 9,
              height: 9,
              borderRadius: 2,
              background: colors.accent,
              boxShadow: `0 0 12px ${colors.accent}`,
            }}
          />
          <div>
            <div style={{ font: `600 15px/1.1 ${font.sans}`, letterSpacing: '0.01em' }}>
              {header.title}
            </div>
            <div
              style={{
                font: `500 10px/1.3 ${font.mono}`,
                color: colors.faint,
                letterSpacing: '0.04em',
                marginTop: 3,
              }}
            >
              {header.subtitle}
            </div>
          </div>
        </div>
        <button
          onClick={onConnectWallet}
          style={{
            font: `500 11px/1 ${font.mono}`,
            color: colors.textDim,
            background: 'transparent',
            border: `1px solid rgba(255,255,255,0.16)`,
            borderRadius: 6,
            padding: '9px 12px',
            cursor: 'pointer',
            letterSpacing: '0.03em',
          }}
        >
          {walletLabel}
        </button>
      </div>

      {/* thread */}
      <div
        ref={scrollRef}
        className="dac-scroll"
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '24px 20px',
          display: 'flex',
          flexDirection: 'column',
          gap: 18,
        }}
      >
        {empty && (
          <div style={{ margin: 'auto', textAlign: 'center', maxWidth: 340, padding: '30px 0' }}>
            <div style={{ font: `500 12px/1.7 ${font.mono}`, color: colors.faint, letterSpacing: '0.04em' }}>
              $ defi-agent --query
            </div>
            <div style={{ font: `400 14px/1.7 ${font.sans}`, color: colors.muted, marginTop: 10 }}>
              Paste a transaction hash or wallet address — I'll resolve cross-chain status, Morpho
              positions, and balances.
            </div>
            <div style={{ font: `400 12px/1.7 ${font.sans}`, color: colors.faint, marginTop: 8 }}>
              Try a suggestion below to begin.
            </div>
          </div>
        )}

        {messages.map((m) => (
          <ChatMessageView key={m.id} message={m} />
        ))}

        {thinking && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 9, animation: 'dac-msgin 0.2s ease' }}>
            <span style={{ font: `500 10px/1 ${font.mono}`, color: colors.faint }}>agent</span>
            <span style={{ display: 'flex', gap: 4 }}>
              <Dot delay={0} />
              <Dot delay={0.2} />
              <Dot delay={0.4} />
            </span>
          </div>
        )}
      </div>

      {/* chips + input */}
      <div style={{ flex: 'none', padding: '14px 20px 18px', borderTop: `1px solid ${colors.line}` }}>
        {suggestions.length > 0 && (
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
            {suggestions.map((s) => (
              <button
                key={s.query}
                onClick={() => onSend(s.query)}
                style={{
                  font: `500 11px/1 ${font.mono}`,
                  color: colors.textDim,
                  background: colors.bubble,
                  border: `1px solid ${colors.line}`,
                  borderRadius: 7,
                  padding: '8px 11px',
                  cursor: 'pointer',
                }}
              >
                {s.label}
              </button>
            ))}
          </div>
        )}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            background: colors.bubble,
            border: `1px solid rgba(255,255,255,0.1)`,
            borderRadius: 9,
            padding: '8px 8px 8px 14px',
          }}
        >
          <input
            className="dac-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                submit();
              }
            }}
            placeholder={placeholder}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              font: `400 13px/1.4 ${font.mono}`,
              color: colors.text,
            }}
          />
          <button
            onClick={submit}
            style={{
              flex: 'none',
              font: `600 11px/1 ${font.mono}`,
              color: colors.bg,
              background: colors.accent,
              border: 'none',
              borderRadius: 6,
              padding: '9px 13px',
              cursor: 'pointer',
              letterSpacing: '0.04em',
            }}
          >
            SEND
          </button>
        </div>
      </div>
    </div>
  );
};