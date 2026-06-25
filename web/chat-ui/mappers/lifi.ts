// Maps a raw LI.FI "status" response into the LifiTransferView consumed by
// <LifiStatusCard />. Tolerant of partial/in-flight responses.
//
//   import { mapLifiStatus } from 'defi-agent-chat-react';
//   const view = mapLifiStatus(await getStatus(...));

import type { LifiTransferView, LifiLegView, TxStatus, LinkRef } from '../types';

/* ---- Raw response shape (subset of the LI.FI status payload) ---- */

export interface LifiRawToken {
  symbol: string;
  decimals: number;
}

export interface LifiRawLeg {
  txHash?: string;
  txLink?: string;
  amount: string;
  amountUSD?: string;
  token: LifiRawToken;
  chainId: number;
  gasAmountUSD?: string;
  timestamp?: number;
}

export interface LifiRawFeeCost {
  name: string;
  amountUSD?: string;
}

export interface LifiStatusResponse {
  sending: LifiRawLeg;
  receiving: LifiRawLeg;
  feeCosts?: LifiRawFeeCost[];
  fromAddress?: string;
  toAddress?: string;
  tool?: string;
  status: string; // DONE | PENDING | FAILED | NOT_FOUND | INVALID
  substatusMessage?: string;
  lifiExplorerLink?: string;
  bridgeExplorerLink?: string;
}

/* ---- Chain metadata ---- */

const CHAIN_NAME: Record<number, string> = {
  1: 'Ethereum',
  10: 'Optimism',
  56: 'BNB Chain',
  137: 'Polygon',
  8453: 'Base',
  42161: 'Arbitrum',
  167000: 'Taiko',
};

const EXPLORER_NAME: Record<number, string> = {
  1: 'Etherscan',
  10: 'OP Etherscan',
  56: 'BscScan',
  137: 'Polygonscan',
  8453: 'Basescan',
  42161: 'Arbiscan',
  167000: 'Taikoscan',
};

const chainName = (id: number) => CHAIN_NAME[id] ?? `Chain ${id}`;
const explorerName = (id: number) => EXPLORER_NAME[id] ?? 'Explorer';

/* ---- Formatting helpers ---- */

export function formatUnits(value: string, decimals: number, maxFrac = 4): string {
  let v = value || '0';
  const neg = v.startsWith('-');
  if (neg) v = v.slice(1);
  let bi: bigint;
  try {
    bi = BigInt(v);
  } catch {
    return value;
  }
  const base = BigInt(10) ** BigInt(decimals);
  const whole = bi / base;
  const frac = bi % base;
  const wholeStr = whole.toLocaleString('en-US');
  let fracStr = frac.toString().padStart(decimals, '0').slice(0, maxFrac).replace(/0+$/, '');
  const out = fracStr ? `${wholeStr}.${fracStr}` : wholeStr;
  return neg ? `-${out}` : out;
}

export function formatUSD(value?: string | number, frac = 2): string {
  const n = typeof value === 'number' ? value : parseFloat(value ?? '0');
  if (!isFinite(n)) return '$0.00';
  return `$${n.toLocaleString('en-US', { minimumFractionDigits: frac, maximumFractionDigits: frac })}`;
}

export function truncateHash(hash?: string, head = 6, tail = 4): string {
  if (!hash) return '—';
  if (hash.length <= head + tail) return hash;
  return `${hash.slice(0, head)}…${hash.slice(-tail)}`;
}

function durationLabel(from?: number, to?: number): string | undefined {
  if (!from || !to || to < from) return undefined;
  const secs = to - from;
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `${m}m ${String(s).padStart(2, '0')}s`;
}

function mapStatus(status: string): TxStatus {
  const s = status.toUpperCase();
  if (s === 'DONE') return 'DONE';
  if (s === 'FAILED' || s === 'INVALID' || s === 'NOT_FOUND') return 'FAILED';
  return 'PENDING';
}

function toolLabel(raw: LifiStatusResponse): string {
  const pretty = (raw.tool ?? 'bridge')
    .replace(/([a-z])([A-Z0-9])/g, '$1 $2')
    .replace(/bus$/i, '')
    .trim()
    .toUpperCase();
  const isLZ = /layerzero/i.test(raw.bridgeExplorerLink ?? '');
  return isLZ ? `${pretty} · LAYERZERO` : pretty;
}

function mapLeg(leg: LifiRawLeg): LifiLegView {
  return {
    chainName: chainName(leg.chainId),
    amount: formatUnits(leg.amount, leg.token.decimals),
    symbol: leg.token.symbol.replace(/\(.*\)/, '').trim(),
    amountUSD: formatUSD(leg.amountUSD),
    txShort: truncateHash(leg.txHash),
    txUrl: leg.txLink ?? '#',
  };
}

function feesLabel(raw: LifiStatusResponse): string {
  const gas =
    parseFloat(raw.sending.gasAmountUSD ?? '0') + parseFloat(raw.receiving.gasAmountUSD ?? '0');
  const parts = [`gas $${gas.toFixed(3)}`];
  const relay = raw.feeCosts?.find((f) => /relay/i.test(f.name));
  if (relay) parts.push(`relay $${parseFloat(relay.amountUSD ?? '0').toFixed(3)}`);
  const lz = raw.feeCosts?.find((f) => /layerzero/i.test(f.name));
  if (lz) parts.push(`lz $${parseFloat(lz.amountUSD ?? '0').toFixed(3)}`);
  return parts.join(' · ');
}

function walletLabel(raw: LifiStatusResponse): string {
  const from = truncateHash(raw.fromAddress, 6, 4);
  if (!raw.toAddress || raw.fromAddress?.toLowerCase() === raw.toAddress?.toLowerCase()) {
    return `${from} → self`;
  }
  return `${from} → ${truncateHash(raw.toAddress, 6, 4)}`;
}

export function mapLifiStatus(raw: LifiStatusResponse): LifiTransferView {
  const links: LinkRef[] = [];
  if (raw.sending.txLink) links.push({ label: explorerName(raw.sending.chainId), url: raw.sending.txLink });
  if (raw.receiving.txLink) links.push({ label: explorerName(raw.receiving.chainId), url: raw.receiving.txLink });
  if (raw.lifiExplorerLink) links.push({ label: 'LI.FI Scan', url: raw.lifiExplorerLink });
  if (raw.bridgeExplorerLink) links.push({ label: 'LayerZero', url: raw.bridgeExplorerLink });

  return {
    status: mapStatus(raw.status),
    statusLabel: (raw.substatusMessage ?? '').replace(/^The /, '').replace(/\.$/, '').toLowerCase() || raw.status.toLowerCase(),
    toolLabel: toolLabel(raw),
    send: mapLeg(raw.sending),
    receive: mapLeg(raw.receiving),
    durationLabel: durationLabel(raw.sending.timestamp, raw.receiving.timestamp),
    feesLabel: feesLabel(raw),
    walletLabel: walletLabel(raw),
    links,
  };
}
