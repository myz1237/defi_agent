import React from 'react';
import { colors, font } from '../theme';
import type { BalancesView, TokenBalance } from '../types';
import { TokenBadge } from './Badges';

const Row: React.FC<{ t: TokenBalance }> = ({ t }) => (
  <div
    style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '9px 8px',
      borderRadius: 6,
    }}
  >
    <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
      <TokenBadge symbol={t.symbol} />
      <div>
        <div style={{ font: `600 12px/1 ${font.sans}`, color: colors.text }}>{t.symbol}</div>
        <div style={{ font: `400 9px/1.3 ${font.mono}`, color: colors.faint, marginTop: 2 }}>
          {t.chainName}
        </div>
      </div>
    </div>
    <div style={{ textAlign: 'right' }}>
      <div style={{ font: `500 12px/1 ${font.mono}`, color: colors.text }}>{t.amount}</div>
      <div style={{ font: `400 9px/1.3 ${font.mono}`, color: colors.faint, marginTop: 2 }}>
        {t.valueUSD}
      </div>
    </div>
  </div>
);

export const TokenBalancesCard: React.FC<{ data: BalancesView }> = ({ data }) => (
  <div
    style={{
      border: `1px solid ${colors.line}`,
      borderRadius: 8,
      background: colors.panel,
      overflow: 'hidden',
      animation: 'dac-msgin 0.3s ease',
    }}
  >
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '11px 14px',
        borderBottom: `1px solid ${colors.lineSoft}`,
      }}
    >
      <span style={{ font: `600 10px/1 ${font.mono}`, color: colors.faint, letterSpacing: '0.1em' }}>
        TOKEN BALANCES · {data.chainCount} {data.chainCount === 1 ? 'CHAIN' : 'CHAINS'}
      </span>
      <span style={{ font: `500 11px/1 ${font.mono}`, color: colors.text }}>{data.totalLabel}</span>
    </div>

    <div style={{ padding: 6 }}>
      {data.tokens.map((t, i) => (
        <Row key={t.symbol + t.chainName + i} t={t} />
      ))}
    </div>
  </div>
);
