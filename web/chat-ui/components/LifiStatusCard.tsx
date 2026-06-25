import React from 'react';
import { colors, font } from '../theme';
import type { LifiTransferView, LifiLegView, TxStatus } from '../types';
import { ChainAvatar } from './Badges';

const STATUS_COLOR: Record<TxStatus, string> = {
  DONE: colors.green,
  PENDING: colors.amber,
  FAILED: colors.red,
};

const microLabel: React.CSSProperties = {
  font: `500 9px/1 ${font.mono}`,
  color: colors.faint,
  letterSpacing: '0.12em',
};

const Leg: React.FC<{ leg: LifiLegView; align?: 'left' | 'right' }> = ({ leg }) => (
  <div>
    <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 7 }}>
      <ChainAvatar chainName={leg.chainName} />
      <span style={{ font: `500 11px/1 ${font.sans}`, color: colors.muted }}>
        {leg.chainName}
      </span>
    </div>
    <div style={{ font: `500 16px/1.1 ${font.mono}`, color: colors.text }}>
      {leg.amount} <span style={{ fontSize: 11, color: colors.muted }}>{leg.symbol}</span>
    </div>
    <div style={{ font: `400 11px/1.4 ${font.mono}`, color: colors.faint, marginTop: 2 }}>
      {leg.amountUSD}
    </div>
    <a
      href={leg.txUrl}
      target="_blank"
      rel="noreferrer"
      style={{
        font: `400 10px/1 ${font.mono}`,
        color: colors.accent,
        textDecoration: 'none',
        display: 'inline-block',
        marginTop: 7,
      }}
    >
      {leg.txShort} ↗
    </a>
  </div>
);

const MetaRow: React.FC<{ label: string; value: string; valueColor?: string }> = ({
  label,
  value,
  valueColor = colors.textDim,
}) => (
  <div
    style={{
      display: 'flex',
      justifyContent: 'space-between',
      gap: 12,
      font: `400 11px/1.3 ${font.mono}`,
    }}
  >
    <span style={{ color: colors.faint, flex: 'none' }}>{label}</span>
    <span style={{ color: valueColor, textAlign: 'right' }}>{value}</span>
  </div>
);

export const LifiStatusCard: React.FC<{ data: LifiTransferView }> = ({ data }) => {
  const statusColor = STATUS_COLOR[data.status];
  return (
    <div
      style={{
        border: `1px solid ${colors.line}`,
        borderRadius: 8,
        background: colors.panel,
        overflow: 'hidden',
        animation: 'dac-msgin 0.3s ease',
      }}
    >
      {/* header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '11px 14px',
          borderBottom: `1px solid ${colors.lineSoft}`,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
          <span
            style={{
              width: 7,
              height: 7,
              borderRadius: '50%',
              background: statusColor,
              boxShadow: `0 0 8px ${statusColor}`,
            }}
          />
          <span
            style={{
              font: `600 10px/1 ${font.mono}`,
              color: statusColor,
              letterSpacing: '0.08em',
            }}
          >
            {data.status}
          </span>
        </div>
        <span style={{ font: `500 9px/1 ${font.mono}`, color: colors.faint, letterSpacing: '0.06em' }}>
          {data.toolLabel}
        </span>
      </div>

      {/* body */}
      <div style={{ padding: '15px 14px' }}>
        <div style={{ ...microLabel, marginBottom: 13 }}>CROSS-CHAIN TRANSFER</div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr auto 1fr',
            alignItems: 'start',
            gap: 8,
          }}
        >
          <Leg leg={data.send} />
          <div style={{ font: `400 16px/1 ${font.mono}`, color: '#4b5160', paddingTop: 24 }}>→</div>
          <Leg leg={data.receive} />
        </div>

        <div style={{ height: 1, background: colors.lineSoft, margin: '14px 0' }} />

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <MetaRow label="STATUS" value={`${data.status} · ${data.statusLabel}`} valueColor={statusColor} />
          {data.durationLabel && <MetaRow label="DURATION" value={data.durationLabel} />}
          <MetaRow label="FEES" value={data.feesLabel} />
          <MetaRow label="WALLET" value={data.walletLabel} />
        </div>
      </div>

      {/* footer links */}
      {data.links.length > 0 && (
        <div
          style={{
            display: 'flex',
            gap: 14,
            flexWrap: 'wrap',
            padding: '10px 14px',
            borderTop: `1px solid ${colors.lineSoft}`,
            background: colors.panelAlt,
          }}
        >
          {data.links.map((l) => (
            <a
              key={l.url + l.label}
              href={l.url}
              target="_blank"
              rel="noreferrer"
              style={{ font: `400 10px/1 ${font.mono}`, color: colors.muted, textDecoration: 'none' }}
            >
              {l.label}
            </a>
          ))}
        </div>
      )}
    </div>
  );
};
