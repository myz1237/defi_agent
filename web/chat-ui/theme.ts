// Design tokens for the DeFi Agent chat UI (Terminal direction).
// Inline-style based — no CSS framework required. Load IBM Plex fonts in your app
// (see README) for an exact match; the stack falls back to system mono/sans otherwise.

export const colors = {
  bg: '#0e1014',
  pageBg: '#090a0d',
  panel: '#14171d',
  panelAlt: '#10131a',
  bubble: '#1b2027',
  hover: '#1a1e25',
  line: 'rgba(255,255,255,0.08)',
  lineSoft: 'rgba(255,255,255,0.06)',
  text: '#e6e8ec',
  textDim: '#cfd3da',
  muted: '#8b919c',
  faint: '#5c626d',
  accent: '#34d7c8',
  accentHi: '#5fe6da',
  green: '#36d399',
  amber: '#f5b13d',
  red: '#f06363',
} as const;

export const font = {
  mono: `'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, monospace`,
  sans: `'IBM Plex Sans', system-ui, -apple-system, Segoe UI, sans-serif`,
} as const;

export type BadgeMeta = { char: string; fg: string; bg: string };
export type ChainMeta = { text: string; fg: string; bg: string };

// Token glyph badges (CSS letter marks — no external logos).
export const tokenBadges: Record<string, BadgeMeta> = {
  USDT: { char: '₮', fg: '#3fd0a0', bg: '#0e3a2c' },
  USDC: { char: '$', fg: '#5e9bff', bg: '#11294f' },
  ETH: { char: 'Ξ', fg: '#9aa6ec', bg: '#1f2545' },
  WETH: { char: 'Ξ', fg: '#9aa6ec', bg: '#1f2545' },
  WSTETH: { char: 'w', fg: '#7fe3ff', bg: '#0b2e3a' },
  WBTC: { char: '₿', fg: '#f0a55a', bg: '#3a2a16' },
  DAI: { char: '◈', fg: '#f3c969', bg: '#3a3216' },
};

export const chainBadges: Record<string, ChainMeta> = {
  ARBITRUM: { text: 'ARB', fg: '#9ec9ff', bg: '#2c374a' },
  TAIKO: { text: 'TKO', fg: '#ff8fc4', bg: '#3a2030' },
  BASE: { text: 'BASE', fg: '#9ec9ff', bg: '#1a2740' },
  ETHEREUM: { text: 'ETH', fg: '#9aa6ec', bg: '#1f2545' },
  OPTIMISM: { text: 'OPT', fg: '#ff9a9a', bg: '#3a2424' },
  BNB: { text: 'BNB', fg: '#f0d27a', bg: '#3a341a' },
  POLYGON: { text: 'POL', fg: '#c9a6ff', bg: '#2a2145' },
};

export function getTokenBadge(symbol: string): BadgeMeta {
  const key = symbol.toUpperCase().replace(/[^A-Z]/g, '');
  return (
    tokenBadges[key] ?? {
      char: (symbol[0] || '?').toUpperCase(),
      fg: colors.textDim,
      bg: '#23272f',
    }
  );
}

export function getChainBadge(name: string): ChainMeta {
  const key = name.toUpperCase().replace(/[^A-Z]/g, '');
  return (
    chainBadges[key] ?? {
      text: name.slice(0, 3).toUpperCase(),
      fg: colors.muted,
      bg: '#23272f',
    }
  );
}
