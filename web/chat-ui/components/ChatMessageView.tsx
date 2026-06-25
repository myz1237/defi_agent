import React from 'react';
import { colors, font } from '../theme';
import type { ChatMessage, AgentCard } from '../types';
import { LifiStatusCard } from './LifiStatusCard';
import { MorphoPositionsCard } from './MorphoPositionsCard';
import { TokenBalancesCard } from './TokenBalancesCard';

// The agent is asked for plain text, but models still emit **bold**/`code`. Strip the common
// markers so they don't show literally in the terminal-style text.
function stripMd(s: string): string {
  return s
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/__(.+?)__/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/^\s{0,3}#{1,6}\s+/gm, '') // headings
    .replace(/^\s*\|?\s*[-:|\s]{3,}\s*$/gm, '') // table separators / --- rules
    .replace(/^\s*\|(.+)\|\s*$/gm, (_m, c: string) =>
      c
        .split('|')
        .map((x) => x.trim())
        .filter(Boolean)
        .join("  "),
    ) // table rows -> spaced
    .replace(/^\s*[-*]\s+/gm, "• ") // bullets
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

const AgentCardView: React.FC<{ card: AgentCard }> = ({ card }) => {
  switch (card.kind) {
    case 'lifi':
      return <LifiStatusCard data={card.data} />;
    case 'morpho':
      return <MorphoPositionsCard data={card.data} />;
    case 'balances':
      return <TokenBalancesCard data={card.data} />;
    default:
      return null;
  }
};

export const ChatMessageView: React.FC<{ message: ChatMessage }> = ({ message }) => {
  if (message.role === 'user') {
    return (
      <div
        style={{
          alignSelf: 'flex-end',
          maxWidth: '78%',
          background: colors.bubble,
          border: `1px solid ${colors.lineSoft}`,
          borderRadius: '11px 11px 3px 11px',
          padding: '10px 13px',
          font: `500 13px/1.45 ${font.sans}`,
          color: colors.textDim,
          wordBreak: 'break-word',
          animation: 'dac-msgin 0.25s ease',
        }}
      >
        {message.text}
      </div>
    );
  }

  // agent
  if ('card' in message) {
    return <AgentCardView card={message.card} />;
  }

  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', animation: 'dac-msgin 0.25s ease' }}>
      <span style={{ flex: 'none', font: `500 10px/1.6 ${font.mono}`, color: colors.accent }}>›</span>
      <div style={{ font: `400 13px/1.6 ${font.sans}`, color: '#a9aeb8', maxWidth: '80%', whiteSpace: 'pre-wrap' }}>
        {stripMd(message.text)}
      </div>
    </div>
  );
};
