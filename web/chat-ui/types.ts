// View-model types consumed by the presentational cards.
// Map your raw LI.FI / Morpho / balances API responses into these shapes.
// (A ready-made LI.FI mapper is provided in ./mappers/lifi.ts.)

export type TxStatus = 'DONE' | 'PENDING' | 'FAILED';

export interface LinkRef {
  label: string;
  url: string;
}

/** One side (source or destination) of a cross-chain transfer. */
export interface LifiLegView {
  chainName: string;
  /** Human-formatted token amount, e.g. "129.49". */
  amount: string;
  symbol: string;
  /** Formatted USD value, e.g. "$129.58". */
  amountUSD: string;
  /** Truncated tx hash for display, e.g. "0xe1ff…d08c". */
  txShort: string;
  txUrl: string;
}

export interface LifiTransferView {
  status: TxStatus;
  /** Short human status, e.g. "transfer complete". */
  statusLabel: string;
  /** Route/tool label, e.g. "STARGATE V2 · LAYERZERO". */
  toolLabel: string;
  send: LifiLegView;
  receive: LifiLegView;
  /** e.g. "10m 06s". Optional — omit for in-flight transfers. */
  durationLabel?: string;
  /** e.g. "gas $0.036 · relay $0.006 · lz $0.030". */
  feesLabel: string;
  /** e.g. "0x204d…3906 → self". */
  walletLabel: string;
  links: LinkRef[];
}

export interface MorphoBorrowMarket {
  collateralSymbol: string;
  loanSymbol: string;
  chainName: string;
  /** e.g. "1.96". Drives the health color (>=1.5 green, >=1.1 amber, else red). */
  healthFactor: string;
  /** e.g. "4.20 wstETH". */
  collateralAmount: string;
  /** e.g. "6,500 USDC". */
  borrowAmount: string;
  /** 0–100, current loan-to-value. */
  ltvPct: number;
  /** 0–100, liquidation LTV. */
  lltvPct: number;
}

export interface MorphoVaultPosition {
  name: string;
  /** e.g. "25,000 USDC deposited". */
  depositLabel: string;
  /** e.g. "7.21%". */
  apyLabel: string;
}

export interface MorphoView {
  /** Truncated address for the header, e.g. "0x204d…3906". */
  address: string;
  /** e.g. "$33.5K". */
  netWorthLabel: string;
  borrowMarkets: MorphoBorrowMarket[];
  vaults: MorphoVaultPosition[];
}

export interface TokenBalance {
  symbol: string;
  chainName: string;
  /** Formatted amount, e.g. "128.67". */
  amount: string;
  /** Formatted USD value, e.g. "$128.77". */
  valueUSD: string;
}

export interface BalancesView {
  /** e.g. "$40,676". */
  totalLabel: string;
  chainCount: number;
  tokens: TokenBalance[];
}

export type AgentCard =
  | { kind: 'lifi'; data: LifiTransferView }
  | { kind: 'morpho'; data: MorphoView }
  | { kind: 'balances'; data: BalancesView };

export type ChatMessage =
  | { id: string; role: 'user'; text: string }
  | { id: string; role: 'agent'; text: string }
  | { id: string; role: 'agent'; card: AgentCard };

export interface Suggestion {
  label: string;
  query: string;
}
