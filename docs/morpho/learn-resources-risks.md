# Risk & Security Documentation

Source: https://docs.morpho.org/learn/resources/risks



By using Morpho or Morpho Vaults, you assume the risks associated. The following section provides an overview of different types of risks you should be aware of when using Morpho and Morpho Vaults. This overview is not exhaustive and may not cover all potential risks to which you might be exposed.
Morpho is committed to use industry-leading security practices. Yet, there are still a number of risks associated with the use of Morpho and Morpho Vaults that users must be aware of.

## Morpho Security practices [#morpho-security-practices]

Morpho is known for its industry-leading security practices and follows a multi-faceted approach to security.

Morpho security practices include formal verification, mutation tests, fuzzing, unit testing, and peer reviews that can be found within respective [Github repositories](https://github.com/morpho-org). External measures include professional security reviews, contests, and pre/post-deployment bounties.

A whole article was dedicated to the [Morpho Security Framework](https://morpho.org/blog/morpho-blue-security-framework-building-the-most-secure-lending-protocol/).

The Morpho apps and smart contracts have been audited extensively by a wide range of security firms, with every new app and feature undergoing audits before release. The full list of audits is available in the [Audits](/get-started/resources/audits/) section.

## Smart Contract Risk [#smart-contract-risk]

There is an inherent risk that the protocol could contain a smart contract vulnerability or bug.

Several security measures are employed to mitigate this risk:

* Core contracts are immutable
* It is a simple and open-sourced [code base](/get-started/resources/contracts/) that avoids complexities
* The code has been audited by multiple auditors, refer to the [security reviews](/get-started/resources/audits/) section
* [Formal verification](/learn/resources/risks/#formal-verifications) has been applied using [Certora](https://www.certora.com/)
* One ongoing bug bounty program: [Cantina - $2,500,000](https://cantina.xyz/bounties/35a5f0a1-2ffd-432c-8f3b-77d169add8c3) (Morpho Blue, Morpho Midnight & Morpho Vaults)

## Oracle Risk [#oracle-risk]

Every Morpho market is connected to an oracle, established at market creation. It is important to understand that no oracle is immune to price manipulation, which can lead to liquidations or even bad debt. However, some oracles will be more resistant and resilient than others.

When assessing the reliability of an oracle, consider factors such as safety and liveness, particularly if the oracle is centralized. Also, take into account the settings and processes pertaining to the definition and frequency of price updates.

Markets with a faulty oracle can lead to loss of assets across Morpho markets and any vault strategy that depends on them.

## Counterparty Risk [#counterparty-risk]

Before entering a market, it's crucial to conduct thorough due diligence on the loan asset and the collateral asset to understand who holds power over them. Factors to consider include centralization, as a centralized governance could blacklist a specific user or even Morpho, resulting in a loss of assets. The distribution of the asset is also important, as a high concentration can cause extreme price fluctuations.

## Liquidation Risk [#liquidation-risk]

### Liquidation Risk (for borrowers) [#liquidation-risk-for-borrowers]

Each Morpho market is linked to an immutable Liquidation Loan-to-Value (LLTV). If the Loan-To-Value of your position exceeds this LLTV, you will face liquidation. When borrowing on Morpho, carefully select the market and diligently manage the health of your position.

### Bad Debt Risk (for lenders) [#bad-debt-risk-for-lenders]

There could be circumstances in which the collateral's value for a position drops below the borrowed amount before liquidators can close the position. In such cases, the borrower holding this position has no incentive to repay the debt. Morpho has different mechanisms for accounting for bad debts. You can read more about it in the [bad debt section](/learn/concepts/liquidation/#bad-debt).

### Liquidity Risk (for lenders) [#liquidity-risk-for-lenders]

Liquidity refers to the access to supplied assets. A lack of liquidity can prevent suppliers from withdrawing their assets for a certain period of time. Liquidity issues are tackled through the interest rate model. Before providing liquidity, it's essential to understand the market's interest rate model. This understanding will help you estimate the level of liquidity you can expect in that market.

## Morpho Vaults Specific Risks [#morpho-vaults-specific-risks]

### Vault Governance Risks [#vault-governance-risks]

Key [roles](/curate/concepts/roles/) within a Morpho Vault V2 wield significant power and can directly affect user interests.

#### Vaults V2 Governance [#vaults-v2-governance]

Vaults V2 introduces a refined role system with clear separation of concerns:

* The **Owner** appoints key roles (Curator and Sentinels) but does not inherit their powers. A compromised Owner can replace the Curator, who controls the vault's strategy.
* The **Curator** configures adapters, caps, fees, allocators, and gates. Most Curator actions are subject to [timelocks](/curate/concepts/timelock/), giving depositors time to react before changes take effect.
* The **Allocators** execute asset allocation between enabled adapters within Curator-set limits. They cannot introduce new risks but can influence yield and liquidity by moving assets between approved yield sources.
* The **Sentinels** provide emergency de-risking capabilities. They can revoke pending timelocked actions, decrease caps, and deallocate assets without being allocators.

**Key governance mechanisms in V2:**

* **Timelocks**: Critical configuration changes require a submission followed by a waiting period before execution. This ensures depositors can always withdraw their assets before changes take effect.
* **Abdication**: The Curator can permanently disable specific timelocked functions via [abdication](/curate/tutorials-v2/abdicate-gates/), irreversibly locking configurations. While this provides strong guarantees against future changes, it also removes flexibility.
* **Gates**: [Gate contracts](/curate/concepts/gates/) can restrict share and asset transfers. A misconfigured gate could lock users out of deposits or withdrawals.
* **Adapter Registry**: Vaults can be restricted to adapters from a specific [registry](/curate/concepts/adapter-registry/). This limits what yield sources the Curator can enable but relies on the registry's governance.
* **Fee Caps**: Performance fees are capped at 50% of interest, and management fees at 5% annually, limiting maximum fee exposure for depositors.

When depositing into a Morpho Vault, it is important to conduct thorough due diligence on the vault's settings and its allocation strategy, as well as to stay up to date with its changes. For legacy Vault V1 governance details, use the archived curator documentation in [Curate](/curate/tutorials-v1/vault-creation/).