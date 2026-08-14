# Oracle

Source: https://docs.morpho.org/learn/concepts/oracle



<figure>
  <ZoomableImage src="/img/homepage/concepts/concepts_oracle_light.png" alt="Morpho IRM Concept" />
</figure>

## What is an Oracle? [#what-is-an-oracle]

Oracles are smart contracts that provide external data, particularly price information, to blockchain applications. In lending protocols like Morpho, oracles provide price data needed to determine what one token is worth relative to another. For example, the oracle of a market is supposedly answering the question: "How many USDC is 1 BTC worth right now?”

## Oracles in Lending Markets [#oracles-in-lending-markets]

Traditional lending protocols rely on oracles to:

* Determine the value of collateral assets
* Calculate borrowing capacity
* Trigger liquidations when positions become undercollateralized
* Enable accurate interest rate calculations

## Oracle Implementation in Morpho [#oracle-implementation-in-morpho]

Morpho takes an **oracle-agnostic approach**, allowing market creators to select the most appropriate price feed mechanisms based on specific market requirements. Each Morpho market specifies its oracle in the market parameters, ensuring that oracle implementations can be tailored to specific asset pairs.

All oracles used in Morpho markets implement the `IOracle` [interface](/get-started/resources/contracts/oracles#price), which has a single, standardized function:

```solidity
function price() external view returns (uint256);
```

This function returns the price of 1 unit of collateral token quoted in the loan token, with appropriate scaling to account for decimal differences between tokens.

## Types of Oracles Compatible with Morpho [#types-of-oracles-compatible-with-morpho]

Various oracle implementations can be used with Morpho markets:

1. **Price Feed Oracles**: Utilize external price feeds (like Chainlink, Redstone, API3, Pyth, Chronicle) to calculate asset exchange rates.
2. **Exchange Rate Oracles**: Specialized for wrapped tokens or rebasing tokens where the exchange rate is deterministic (like wstETH/stETH).
3. **Fixed-Price Oracles**: Used for assets with known or predefined exchange rates, such as stablecoins pegged to the same value.

## MorphoChainlinkOracleV2: A Reference Implementation [#morphochainlinkoraclev2-a-reference-implementation]

One reference implementation available is `MorphoChainlinkOracleV2`, which leverages Chainlink-compliant price feeds while supporting multiple routing configurations:

* Direct feeds (e.g., stETH/ETH)
* Inverse feeds (e.g., ETH/USDC → USDC/ETH)
* Multiple feed routes (e.g., stETH/USD and USDC/USD)
* Complex routing with multiple hops

This implementation demonstrates the flexibility of the oracle system within Morpho, allowing markets to maintain accurate pricing even when direct price feeds aren't available.

## Deploy an Oracle [#deploy-an-oracle]

<Callout type="info">
  Please refer to this section of the documentation to deploy a new oracle:
  [Deploy an Oracle](/curate/tutorials-market-v1/deploying-oracle/)
</Callout>

## Key Oracle Characteristics in Morpho Markets [#key-oracle-characteristics-in-morpho-markets]

* **Purpose-Built**: Each oracle returns the specific exchange rate between a collateral asset and a loan asset
* **Immutable**: Once a market is deployed, its oracle address cannot be modified
* **Independent**: Each oracle operates autonomously and can use different pricing sources
* **Flexible Implementation**: Curators can leverage various data sources while maintaining a consistent interface

## Oracle Selection by Market Curators [#oracle-selection-by-market-curators]

Market curators (not Morpho) are responsible for selecting and implementing appropriate oracles for their markets. Each Morpho market specifies its oracle in the market parameters:

`CollateralAsset/LoanAsset (LLTV%, OracleAddress, IRMAddress)`

## Oracle Security Considerations [#oracle-security-considerations]

The security of an oracle is critical to the safety of a Morpho Market. Users should:

* Verify the oracle implementation for any market they interact with
* Understand the price sources being used
* Consider potential manipulation vectors or failure modes

The immutable nature of Morpho Markets means oracle selection is a permanent decision that defines the market's [risk profile](/learn/resources/risks/)

## Oracle community section [#oracle-community-section]

<Callout type="error">
  Some community members contributed to adapters that could be plugged into oracles.

  * Morpho Association nor author of the repository cannot be held responsible for any losses or damages that may result from the use of this information.
  * Users are advised to conduct their own research and exercise caution when applying any strategies or methods described herein.

  If you are fine with it, jump on the liquidation community section [here](/developers/ecosystem/oracles/)
</Callout>