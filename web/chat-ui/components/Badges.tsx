import React from 'react';
import { font, getTokenBadge, getChainBadge } from '../theme';

/** Circular token glyph badge (CSS letter mark). */
export const TokenBadge: React.FC<{ symbol: string; size?: number }> = ({
  symbol,
  size = 24,
}) => {
  const b = getTokenBadge(symbol);
  return (
    <span
      aria-hidden
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        background: b.bg,
        color: b.fg,
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        font: `600 ${Math.round(size * 0.38)}px/1 ${font.mono}`,
        flex: 'none',
      }}
    >
      {b.char}
    </span>
  );
};

/** Circular chain avatar with a 3-letter code (e.g. ARB, TKO). */
export const ChainAvatar: React.FC<{ chainName: string; size?: number }> = ({
  chainName,
  size = 22,
}) => {
  const c = getChainBadge(chainName);
  return (
    <span
      aria-hidden
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        background: c.bg,
        color: c.fg,
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        font: `600 ${Math.round(size * 0.34)}px/1 ${font.mono}`,
        flex: 'none',
      }}
    >
      {c.text}
    </span>
  );
};

/** Small rounded chain tag (e.g. the BASE pill in the Morpho card). */
export const ChainPill: React.FC<{ chainName: string }> = ({ chainName }) => {
  const c = getChainBadge(chainName);
  return (
    <span
      style={{
        font: `500 9px/1 ${font.mono}`,
        color: c.fg,
        background: c.bg,
        padding: '3px 6px',
        borderRadius: 4,
        letterSpacing: '0.04em',
      }}
    >
      {c.text}
    </span>
  );
};
