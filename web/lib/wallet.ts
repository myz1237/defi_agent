// SIWE wallet connect via injected wallet (e.g. MetaMask). Gas-free signature, read-only.

import { API_BASE } from "./api";

export type WalletSession = { address: string; token: string };

function getEthereum(): any {
  const eth = (typeof window !== "undefined" && (window as any).ethereum) || null;
  if (!eth) throw new Error("No injected wallet found. Install MetaMask or a compatible wallet.");
  return eth;
}

function buildSiweMessage(address: string, nonce: string): string {
  const domain = window.location.host;
  const uri = window.location.origin;
  const issued = new Date().toISOString();
  return [
    `${domain} wants you to sign in with your Ethereum account:`,
    address,
    "",
    "Sign in to DeFi Agent (read-only).",
    "",
    `URI: ${uri}`,
    "Version: 1",
    "Chain ID: 1",
    `Nonce: ${nonce}`,
    `Issued At: ${issued}`,
  ].join("\n");
}

export async function connectWallet(): Promise<WalletSession> {
  const eth = getEthereum();
  const accounts: string[] = await eth.request({ method: "eth_requestAccounts" });
  const address = accounts[0];

  const { nonce } = await fetch(`${API_BASE}/v1/auth/nonce`).then((r) => r.json());
  const message = buildSiweMessage(address, nonce);
  const signature: string = await eth.request({ method: "personal_sign", params: [message, address] });

  const resp = await fetch(`${API_BASE}/v1/auth/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, signature }),
  });
  if (!resp.ok) throw new Error(`SIWE verify failed: HTTP ${resp.status}`);
  const data = await resp.json();
  return { address: data.address, token: data.token };
}
