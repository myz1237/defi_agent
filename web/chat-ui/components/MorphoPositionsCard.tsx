import React from 'react';
import { colors, font } from '../theme';
import type { MorphoView, MorphoBorrowMarket, MorphoVaultPosition } from '../types';
import { ChainPill } from './Badges';

function healthColor(hf: string): string {
  const n = parseFloat(hf);
  if (!isFinite(n)) return colors.muted;
  if (n >= 1.5) return colors.green;
  if (n >= 1.1) return colors.amber;
  return colors.red;
}

const sectionLabel: React.CSSProperties = {
  font: `500 9px/1 ${font.mono}`,
  color: colors.faint,
  letterSpacing: '0.12em',
};

const BorrowCard: React.FC<{ m: MorphoBorrowMarket }> = ({ m }) => {
  const used = Math.max(0, Math.min(100, m.lltvPct > 0 ? (m.ltvPct / m.lltvPct) * 100 : 0));
  return (
    <div style={{ border: `1px solid ${colors.line}`, borderRadius: 7, padding: 12 }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 11,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ font: `600 12px/1 ${font.sans}`, color: colors.text }}>
            {m.collateralSymbol} / {m.loanSymbol}
          </span>
          <ChainPill chainName={m.chainName} />
        </div>
        <span style={{ font: `500 10px/1 ${font.mono}`, color: healthColor(m.healthFactor) }}>
          HF {m.healthFactor}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '9px 14px' }}>
        <Field label="COLLATERAL" value={m.collateralAmount} />
        <Field label="BORROW" value={m.borrowAmount} />
      </div>

      <div style={{ marginTop: 12 }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            font: `400 9px/1 ${font.mono}`,
            color: colors.faint,
            marginBottom: 5,
          }}
        >
          <span>LTV {m.ltvPct.toFixed(1)}%</span>
          <span>LLTV {m.lltvPct.toFixed(1)}%</span>
        </div>
        <div style={{ height: 5, borderRadius: 3, background: '#23272f', overflow: 'hidden' }}>
          <div style={{ width: `${used}%`, height: '100%', background: colors.accent, borderRadius: 3 }} />
        </div>
      </div>
    </div>
  );
};

const Field: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div>
    <div style={{ font: `400 9px/1 ${font.mono}`, color: colors.faint, letterSpacing: '0.06em' }}>
      {label}
    </div>
    <div style={{ font: `500 13px/1.3 ${font.mono}`, color: colors.text, marginTop: 3 }}>{value}</div>
  </div>
);

const VaultRow: React.FC<{ v: MorphoVaultPosition }> = ({ v }) => (
  <div
    style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      border: `1px solid ${colors.line}`,
      borderRadius: 7,
      padding: 12,
    }}
  >
    <div>
      <div style={{ font: `600 12px/1.1 ${font.sans}`, color: colors.text }}>{v.name}</div>
      <div style={{ font: `400 10px/1.3 ${font.mono}`, color: colors.faint, marginTop: 2 }}>
        {v.depositLabel}
      </div>
    </div>
    <div style={{ textAlign: 'right' }}>
      <div style={{ font: `600 13px/1 ${font.mono}`, color: colors.green }}>{v.apyLabel}</div>
      <div style={{ font: `400 9px/1 ${font.mono}`, color: colors.faint, marginTop: 3 }}>APY</div>
    </div>
  </div>
);

export const MorphoPositionsCard: React.FC<{ data: MorphoView }> = ({ data }) => (
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
        MORPHO POSITIONS · {data.address}
      </span>
      <span style={{ font: `500 11px/1 ${font.mono}`, color: colors.text }}>{data.netWorthLabel}</span>
    </div>

    <div style={{ padding: 14 }}>
      {data.borrowMarkets.length > 0 && (
        <>
          <div style={{ ...sectionLabel, marginBottom: 10 }}>BORROW MARKET</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {data.borrowMarkets.map((m, i) => (
              <BorrowCard key={i} m={m} />
            ))}
          </div>
        </>
      )}

      {data.vaults.length > 0 && (
        <>
          <div style={{ ...sectionLabel, margin: '16px 0 10px' }}>EARN VAULT</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {data.vaults.map((v, i) => (
              <VaultRow key={i} v={v} />
            ))}
          </div>
        </>
      )}
    </div>
  </div>
);
