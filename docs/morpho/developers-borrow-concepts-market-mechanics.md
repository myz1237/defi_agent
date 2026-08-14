# Market Mechanics

Source: https://docs.morpho.org/developers/borrow/concepts/market-mechanics



Interacting with Morpho Markets involves a set of core functions and concepts that govern how assets are supplied, borrowed, and tracked. Unlike ERC4626 vaults, which have a standardized interface, Morpho's market interactions are defined by its unique internal accounting system.

This page explains the fundamental mechanics you need to understand to build a robust borrowing integration.

## Core Data Structures [#core-data-structures]

At the heart of Morpho are two key structs that define the state of every market and every user's position within it.

### `Market` Struct [#market-struct]

This struct tracks the overall state of a single, isolated market.

```solidity
struct Market {
    uint128 totalSupplyAssets;
    uint128 totalSupplyShares;
    uint128 totalBorrowAssets;
    uint128 totalBorrowShares;
    uint128 lastUpdate;
    uint128 fee;
}
```

* `totalSupply/BorrowAssets`: The total amount of the underlying token supplied or borrowed. This value changes as interest accrues.
* `totalSupply/BorrowShares`: The total number of internal accounting units (shares) held by suppliers or borrowers. This value only changes with user interactions.

### `Position` Struct [#position-struct]

This struct tracks an individual user's position within a specific market.

```solidity
struct Position {
    uint256 supplyShares;
    uint128 borrowShares;
    uint128 collateral;
}
```

* `collateral`: The amount of collateral the user has supplied *to this specific market*.

## Assets vs. Shares: The Core Mechanic [#assets-vs-shares-the-core-mechanic]

The most critical concept to grasp is the relationship between **Assets** and **Shares**. This dual-accounting system is how Morpho manages positions and accrues interest.

### Assets [#assets]

* **Definition**: The actual, underlying tokens (e.g., USDC, WETH) that users interact with.
* **Use Case**: Ideal for user-facing interactions where a specific token amount is desired (e.g., "I want to borrow 1,000 USDC").

### Shares [#shares]

* **Definition**: Internal, non-transferable accounting units that represent a user's proportional stake in the market's total supply or debt.
* **How it works**: When you supply assets, you "buy" shares at the current exchange rate. As interest accrues in the market, the value of each share (its exchange rate back to assets) increases.
* **Use Case**: Ideal for protocol-level interactions and for ensuring full repayment or withdrawal, as it avoids rounding errors ("dust").

### The Relationship: Share Price [#the-relationship-share-price]

The "price" of a share is its exchange rate to the underlying asset. This price is dynamic and increases as interest accrues.

```solidity
// This is a conceptual calculation; the contract uses SharesMathLib for precision.
sharePrice = totalAssets / totalShares;
```

* For **suppliers**, the value of their shares grows over time, representing their earned yield.
* For **borrowers**, the asset value of their debt grows over time, representing the interest they owe.

## Core Functions & Their Dual Nature [#core-functions--their-dual-nature]

Most core functions in Morpho allow you to specify an amount in either `assets` or `shares`. You must provide a value for one and zero for the other.

### `supply` and `borrow` [#supply-and-borrow]

```solidity
function supply(uint256 assets, uint256 shares, ...);
function borrow(uint256 assets, uint256 shares, ...);
```

* **Use `assets` > 0, `shares` = 0:** When a user wants to supply or borrow a precise amount of tokens. This is the most common use case for dApps.
* **Use `assets` = 0, `shares` > 0:** For advanced use cases where you need to mint a precise number of shares.

### `repay` and `withdraw` [#repay-and-withdraw]

```solidity
function repay(uint256 assets, uint256 shares, ...);
function withdraw(uint256 assets, uint256 shares, ...);
```

* **Use `assets` > 0, `shares` = 0:** For partial repayments or withdrawals where a specific token amount is needed.
* **Use `assets` = 0, `shares` > 0:** &#x2A;*Recommended for full repayments/withdrawals.** By specifying the user's exact share balance, you ensure their position is completely closed without leaving dust.

## Collateral and Health [#collateral-and-health]

* **`supplyCollateral` & `withdrawCollateral`**: These functions are straightforward and only operate on `assets`. Collateral in Morpho does not earn yield and thus does not use a share-based system.
* **Position Health**: A user's ability to borrow or withdraw collateral is determined by their Health Factor, which is a function of their collateral value, debt value, and the market's `lltv`.

<Callout type="info">
  To learn more about how position health is calculated and managed, see the &#x2A;*[Collateral, LTV & Health concept page](/developers/borrow/concepts/ltv/)**.
</Callout>

## Practical Implementation Snippets [#practical-implementation-snippets]

### Supplying Collateral & Borrowing (Asset-First) [#supplying-collateral--borrowing-asset-first]

```typescript
// Conceptual TypeScript using a web3 library like Viem

// 1. Approve collateral tokens
await client.writeContract({ functionName: 'approve', args: [morphoAddress, collateralAmount] });

// 2. Supply collateral
await client.writeContract({ functionName: 'supplyCollateral', args: [marketParams, collateralAmount, userAddress] });

// 3. Borrow assets
const { result } = await client.simulateContract({
  functionName: 'borrow',
  args: [marketParams, borrowAmount, 0, userAddress, userAddress] // assets > 0, shares = 0
});
await client.writeContract(result.request);
```

### Full Repayment (Shares-First) [#full-repayment-shares-first]

```typescript
// 1. Fetch the user's current borrow shares
const { borrowShares } = await client.readContract({
  functionName: 'position',
  args: [marketId, userAddress]
});

// 2. Approve the loan token for repayment
// The amount to approve should be slightly more than the expected asset value of the shares
// to account for interest accrued since the last block.
const repayAmountAssets = await client.readContract({
    functionName: 'toAssetsUp', // using a helper or SDK function
    args: [borrowShares, market.totalBorrowAssets, market.totalBorrowShares]
});
await client.writeContract({ functionName: 'approve', args: [morphoAddress, repayAmountAssets] });

// 3. Repay the full debt by specifying the exact shares
await client.writeContract({
    functionName: 'repay',
    args: [marketParams, 0, borrowShares, userAddress] // assets = 0, shares > 0
});
```

## Best Practices [#best-practices]

* **For User-Facing Actions**: Use the `assets` parameter for `supply`, `borrow`, and partial `repay`/`withdraw` as it's more intuitive for users.
* **For Closing Positions**: Use the `shares` parameter for full `repay` and `withdraw` operations to ensure the position is fully closed.
* **Slippage**: When converting between assets and shares, be aware of potential slippage due to interest accrual between transaction simulation and execution.
* **Interest Accrual**: Remember that `totalBorrowAssets` and `totalSupplyAssets` are only updated when an interaction triggers `_accrueInterest`. For the most up-to-date values, use a library like `MorphoBalancesLib` or the Morpho SDK.

By understanding these core mechanics, you can build safe, efficient, and user-friendly applications on top of Morpho Markets.