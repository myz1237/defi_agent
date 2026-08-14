# Variable Rate Market (Morpho Blue)

Source: https://docs.morpho.org/learn/concepts/blue



<figure>
  <ZoomableImage src="/img/homepage/concepts/concepts_market_light.png" alt="Morpho Market Concept" />
</figure>

## What is a Variable Rate Market? [#what-is-a-variable-rate-market]

A variable rate market is a primitive lending pool that pairs one collateral asset with one loan asset. Each market is isolated (meaning risks are contained within each individual market), immutable (cannot be changed after deployment), and will persist as long as the blockchain it deployed on is live. This design ensures predictable behavior and eliminates systematic for lenders and borrowers.
Creating a Morpho Market is **permissionless**.

## Key Features [#key-features]

* **Simple Structure**: One collateral asset, one loan asset per market
* **Permanent Parameters**: Once created, rules never change
* **Isolated Risk**: Each market operates independently
* **Permissionless**: New market doesn’t require governance vote to be created - more [here](/learn/concepts/blue/#permissionless-market-creation)
* **Transparent Rules**: Clear conditions for lending and borrowing

## Market Identification [#market-identification]

Markets follow this naming format:

`CollateralAsset/LoanAsset (LLTV%, OracleAddress, IRMAddress)`

For example: `wstETH/WETH (94.5%, ChainlinkOracleV2-wstETHToWETH, AdaptiveCurveIRM)`

## The Five Parameters [#the-five-parameters]

1. **Collateral Asset** that should be [ERC20 compliant](https://docs.openzeppelin.com/contracts/4.x/erc20) (except that it can omit return values on `transfer` and `transferFrom`.)
2. **Loan Asset** sharing same properties as collateral asset. However, the Loan asset should not be [ERC4626 compliant](https://docs.openzeppelin.com/contracts/4.x/erc4626).
3. **LLTV (Liquidation Loan-To-Value)**: Maximum borrowing percentage before liquidation risk. E.g: LLTV of 80% means for a collateral value equivalent of $100, the maximum one can borrow in value is $80. If above like $80.0001, the position is liquidatable.
4. **Oracle**: Smart contract address pricing the collateral against the loan asset.
5. **IRM (Interest Rate Model)**: Smart contract address containing the formula for determining interest rate paid by borrowers.

## Governance-Approved LLTV & IRM [#governance-approved-lltv--irm]

### LLTVs [#lltvs]

| LLTV (%) | Solidity Values (scaled by 1e18) |
| -------- | -------------------------------- |
| 0        | 0                                |
| 38.5     | 385000000000000000               |
| 62.5     | 625000000000000000               |
| 77.0     | 770000000000000000               |
| 86.0     | 860000000000000000               |
| 91.5     | 915000000000000000               |
| 94.5     | 945000000000000000               |
| 96.5     | 965000000000000000               |
| 98.0     | 980000000000000000               |

### IRM [#irm]

The only Interest Rate Model (IRM) that has been governance-approved is the
[AdaptiveCurveIRM](/learn/concepts/irm/).

## Market ID Generator [#market-id-generator]

Use this tool to generate a unique market ID from your market parameters:

<MarketIdGenerator showExample="true" />

## Permissionless market creation [#permissionless-market-creation]

A distinctive feature of Morpho is permissionless market creation: the protocol allows users to create isolated markets consisting of the five aforementioned parameters.

This a departure from the existing paradigm and traditional lending platforms which:

1. Require governance approval for asset listing and parameter changes.
2. Pool assets into a single lending pool, sharing risk across the entire protocol.

In Morpho, each parameter is selected at market creation and persists in perpetuity. Or, in other words, are immutable. The LLTV and interest rate model must be chosen from a set of options approved by Morpho Governance.

## Core Interactions [#core-interactions]

* **Supply**: Lenders deposit loan assets into a specific market to earn interest.
* **Borrow**: Borrowers supply collateral to the same market and borrow loan assets against it, up to the LLTV limit.
* **Withdraw**: Lenders can withdraw their supplied assets and accrued interest, provided there is enough liquidity in the market.
* **Repay**: Borrowers can repay their loan to reclaim their collateral.
* **Liquidate**: If a borrower's position exceeds the LLTV, anyone can liquidate it by repaying a portion of the debt in exchange for a discounted portion of the collateral.