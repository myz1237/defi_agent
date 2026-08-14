# Morpho Vault V2

Source: https://docs.morpho.org/learn/concepts/vault-v2



<figure>
  <ZoomableImage src="/img/build/earn/morpho-v2-archi-1.png" alt="Morpho Market Concept" />
</figure>

**Morpho Vault V2** is Morpho's permissionless vault framework for curated lending strategies. It is designed around **Adapters**, a granular **ID & Cap System**, and automatic interest accrual through **real-time asset reporting**.

<Callout type="info">
  Morpho Vault V2 is the primary vault surface documented in the Learn section. It builds on the core variable yield generation model while extending it through adapters, granular IDs and caps, and real-time asset reporting. If you need legacy Vault V1 reference material, use the archived curator docs in [Curate](/curate/tutorials-v1/vault-creation/).
</Callout>

## Why Vault V2 Matters [#why-vault-v2-matters]

Morpho Vault V2 is designed for flexibility and control:

* **Universal yield routing**: Curators can enable approved adapters rather than hard-coding a single yield source.
* **Automatic aggregation**: Adapters report current assets through `realAssets()`, allowing the vault to aggregate value across positions in real time.
* **Granular risk controls**: Curators can set both absolute and relative caps on abstract risk identifiers such as collateral, oracle, or protocol exposures.
* **Role separation**: Owner, Curator, Allocator, and Sentinel responsibilities are clearly separated for stronger operational security.
* **Built-in gating and liquidity controls**: Vault V2 supports optional gates, idle assets, liquidity adapters, and in-kind redemption flows.

## Core Concepts of Morpho Vault V2 [#core-concepts-of-morpho-vault-v2]

### 1. The Adapter Model: A Universal Gateway to Yield [#1-the-adapter-model-a-universal-gateway-to-yield]

The central innovation of Morpho Vault V2 is the **Adapter** system. An adapter is a smart contract that acts as a translator, containing the logic to interact with a specific protocol and automatically report the current value of allocated assets.

* **How it works**: The `Allocator` calls `allocate` on the vault, specifying a target adapter, an amount, and any protocol-specific data. The vault then transfers assets to the adapter, which executes the supply logic on the selected yield source, including underlying Morpho variable rate markets and future Morpho markets.
* **Automatic Asset Reporting**: Each adapter implements a `realAssets()` function that returns the current value of all allocated assets it manages. This allows the vault to automatically calculate total assets by aggregating across all adapters.
* **Future-Proof**: New adapters can be developed and enabled by the `Curator` at any time, allowing the vault to integrate with new sources of onchain yield without requiring an upgrade to the vault itself. Current example includes `MorphoMarketV1AdapterV2`.

### 2. Granular Risk Curation: The ID & Cap System [#2-granular-risk-curation-the-id--cap-system]

Morpho Vault V2 introduces a far more sophisticated system for curating risk. Instead of a single cap per market, Curators can now define and cap risk based on abstract identifiers (`ids`), where each `id` represents a common risk factor.

For example, the `MorphoMarketV1AdapterV2` can generate `ids` for:

* A specific collateral asset (e.g., `keccak256("collateralToken", stETH_address)`)
* A specific market configuration (e.g., `keccak256("collateralToken/oracle/lltv", ...)`).

The `Curator` can then set both **absolute caps** (a fixed asset amount) and **relative caps** (a percentage of the vault's total assets) on these `ids`. This allows for multi-dimensional risk policies, such as:

* Max total exposure to `stETH` as collateral: 15M (absolute cap on the collateral `id`).
* Max 20% of the vault allocated to any market using a specific, new oracle (relative cap).

### 3. Advanced Liquidity Curation [#3-advanced-liquidity-curation]

Morpho Vault V2 separates idle liquidity from allocated capital more explicitly.

* **Idle Assets**: All user deposits and withdrawals flow through the main vault contract, which holds the idle assets.
* **Liquidity Adapter**: The `Allocator` can designate a specific, highly liquid adapter as the `liquidityAdapter`. If idle assets are insufficient to cover a withdrawal, the vault will automatically pull assets from this market. This adapter also receives all new deposits, ensuring assets are immediately put to work.
* **In-Kind Redemptions (`forceDeallocate`)**: As a final noncustodial guarantee, users can `forceDeallocate` assets from any adapter back to the vault's idle pool. By combining this with a flash loan, a user can always exit the vault by exchanging their vault receipt tokens for a direct position in an underlying protocol, even if the vault is illiquid. A small penalty applies to disincentivize misuse of this emergency function.

<Callout type="warn">
  Some gate implementations can affect noncustodiality guarantees by preventing certain users from depositing to or withdrawing from the vault.
</Callout>

## Advanced Role System [#advanced-role-system]

Morpho Vault V2 refines the role system for greater security and flexibility:

* **Owner**: Controls top-level permissions. Can appoint the Curator and Sentinels. Has no direct control over assets or risk parameters.
* **Curator**: The risk configuration role. Configures adapters, caps, fees, and interest rate limits. Most actions are timelocked.
* **Allocator**: The active execution role. Allocates assets to enabled adapters and configures the `liquidityAdapter`.
* **Sentinel**: The safety-focused role that can reactively reduce risk by deallocating assets, decreasing caps, or revoking pending timelocked actions.

## Other Key Features [#other-key-features]

* **New Fee Structure**: Supports both a **performance fee** (up to 50% on yield) and a **management fee** (up to 5% on total assets).
* **Interest Rate Controls**: The Allocator can set a `maxRate` that caps how quickly `totalAssets` can grow, useful for implementing capped rate distributions.
* **Gating & Compliance**: Optional `Gate` contracts can be set by the Curator to enforce onchain rules for deposits, withdrawals, and receipt token transfers (e.g., for KYC/whitelisting).

### Fee Wrappers [#fee-wrappers]

A **Fee Wrapper** is a specialized use of Vault V2: a lightweight vault configured to wrap
a single existing Morpho Vault V2, adding a fee layer for distribution channels. The adapter
configuration is permanently locked at deployment, making the wrapper immutably bound to its
child vault. Fee Wrappers enable B2B distribution, per-customer vaults, and white-label products
with configurable performance and management fees.

For detailed documentation on Fee Wrapper architecture, deployment, and integration,
see the [Fee Wrapper concept page](/developers/earn/concepts/fee-wrapper).

## Is Morpho Vault V2 Non-Custodial? [#is-morpho-vault-v2-non-custodial]

**Yes, Morpho Vault V2 maintains noncustodial guarantees through three fundamental mechanisms: in-kind redemptions, timelocks, and role-based access control.**

<Callout type="info">
  Some [gate](#gates-optional-access-control) implementations can affect noncustodiality guarantees by preventing certain users from depositing to or withdrawing from the vault.
</Callout>

### Core Non-Custodial Mechanisms [#core-non-custodial-mechanisms]

#### 1. In-Kind Redemptions with `forceDeallocate` [#1-in-kind-redemptions-with-forcedeallocate]

In-kind redemption in Morpho Vault V2 transfers a user’s position from the vault itself to one of its underlying adapters. It does not withdraw assets out of the Morpho protocol; instead, it shifts the user’s exposure from the vault to the underlying positions, even when those positions are illiquid.

This transition happens through the permissionless `forceDeallocate` function. This mechanism enables:

* **Guaranteed exits**: Users can redeem their Morpho Vault V2 receipt tokens directly for underlying positions in protocols, similar to ETF redemptions
* **Permissionless operation**: Anyone can call `forceDeallocate` to move assets from adapters back to the vault's idle assets
* **Flashloan-enabled exits**: Users can flashloan liquidity, supply it to an adapter's market, then withdraw through `forceDeallocate` before repaying the flashloan

**Complete In-Kind Redemption Workflow:**

When a vault lacks sufficient idle liquidity for withdrawals, users can perform an in-kind redemption through flashloan-enabled exits:

1. **User flashloans the required liquidity amount**
2. **User deposits flashloaned assets directly into the underlying market/protocol**
3. **User calls `forceDeallocate` to withdraw equivalent assets from the adapter**
4. **User withdraws the deallocated assets from the vault**
5. **User repays the flashloan with the withdrawn assets**
6. **User retains their position in the underlying market as compensation**

A small penalty (up to 2%) may apply to discourage manipulation, but this doesn't prevent exits-it only adds a minor cost.

This mechanism ensures that even if a vault's underlying markets become illiquid, users are never permanently locked in it. They can always exit by effectively swapping their vault receipt tokens for direct positions in the underlying protocols.

#### 2. Comprehensive Timelock System [#2-comprehensive-timelock-system]

All potentially harmful curator actions are protected by configurable timelocks (0 to 3 weeks), giving users time to react:

**Timelocked actions include:**

* Increasing allocation caps (absolute and relative)
* Enabling new adapters or allocators
* Setting performance/management fees (capped at 50% and 5% respectively)
* Configuring access gates
* Modifying fee recipients

**Timelock properties:**

* Users can monitor pending changes via the `submit` function, which records proposal timestamps in the `executableAt` mapping
* Sentinels can revoke malicious proposals before execution
* Emergency functions like decreasing caps can be called immediately by curators or sentinels for protective risk management
* Some timelocks can be made infinite through `abdicate`, permanently preventing certain actions

**Key protection:** The timelock system ensures that users always have advance notice of changes that could affect their assets, with emergency overrides only available for actions that reduce risk exposure (like lowering caps), never for actions that could increase risk.

#### 3. Role Separation and Limitations [#3-role-separation-and-limitations]

Morpho Vault V2's role-based architecture ensures no single party can unilaterally harm users through strict separation of concerns, ensuring that even if one role is compromised, user assets remain protected by the constraints and oversight of other roles, combined with timelock protection for any potentially harmful changes.

Check the roles declination on the related [section](/curate/concepts/roles/#morpho-vaults-v2-roles).

### Additional Safety Mechanisms [#additional-safety-mechanisms]

#### Caps and Risk Controls [#caps-and-risk-controls]

* **Absolute caps**: Hard limits on allocation to specific protocols/markets
* **Relative caps**: Percentage-based limits relative to total vault assets
* **Id system**: Groups related risks (e.g., same collateral) under unified caps

#### Gates (Optional Access Control) [#gates-optional-access-control]

When enabled, gates control:

* Receipt token transfers (who can send/receive vault receipt tokens)
* Asset deposits (who can deposit into vault)
* Asset withdrawals (who can receive assets from vault)

Gates are timelocked and can be permanently disabled through abdication.

### Adapter Registry [#adapter-registry]

**Morpho Vaults V2** use the **Morpho Registry**, the official adapter registry maintained by Morpho governance. This registry defines which adapters are approved for use, ensuring that deposits stay within Morpho-reviewed protocols.

When the curator locks (abdicates) the registry, it can never be changed-giving users a strong, permanent guarantee about where their assets can be allocated.

Morpho Vaults V2 benefit from the full support of Morpho's infrastructure:

* **Full app integration**: Listed in the [Morpho app](https://app.morpho.org) (subject to listing process).
* **Curation tools**: Configurable through the [Curator app](https://curator.morpho.org).
* **Data utilities**: [Morpho GraphQL API](https://api.morpho.org/graphql), [Dune Analytics Dashboards](https://dune.com/morpho).
* [Security audits](/get-started/resources/audits/) for all supported contracts and flows.
* Thorough product and technical documentation.
* Peripheral utilities like the [Oracle tester and decoder](https://oracles.morpho.dev/).

#### Immutable Contracts [#immutable-contracts]

All vault contracts are immutable-no upgrades can change the core noncustodial guarantees after deployment.

### Why This Matters [#why-this-matters]

These mechanisms ensure that:

1. **No entity can permanently lock user assets** (guaranteed via `forceDeallocate`)
2. **No surprise changes can harm users** (guaranteed via timelocks)
3. **No single party controls user assets** (guaranteed via role separation)

The combination of guaranteed exits, transparent timelocks, and distributed control makes Morpho Vaults V2 genuinely noncustodial-users retain ultimate control over their assets even when delegating configuration to curators and allocators.