# Collateral, LTV & Health

Source: https://docs.morpho.org/developers/borrow/concepts/ltv



When a user borrows from a Morpho Market, their position's safety is determined by the relationship between their collateral, their debt, and the market's risk parameters. Understanding and clearly displaying these metrics is one of the most critical responsibilities when building a borrow integration.

This page explains the core concepts of Collateral, Loan-to-Value (LTV), and Health Factor.

## Collateral [#collateral]

In Morpho, **collateral** is the asset a user supplies to a market to secure their loan. For example, in a `wstETH/WETH` market, `wstETH` is the collateral. This collateral can protect lenders by enabling the protocol to recover assets if the borrower defaults.

A user's collateral is specific to each market; it is not cross-margined at the market level. Also, the action to supply collateral does not generate yield.

## Understanding Loan-To-Value (LTV) [#understanding-loan-to-value-ltv]

It's essential to understand how LTV is calculated and what it represents.

### How to Calculate LTV [#how-to-calculate-ltv]

The Loan-To-Value (LTV) ratio is a key risk metric that measures the proportion of debt relative to collateral value. To calculate the LTV of a position on Morpho, use the following formula:

$$
\text{LTV} = \frac{\text{BORROWED\_AMOUNT}}{\text{COLLATERAL\_VALUE\_IN\_LOAN\_TOKEN}} \times 100\%
$$

<DocsDefinitionCard title="Where:">
  * **`BORROWED_AMOUNT`** The amount of borrowed assets of the user (in token base units)
  * **`COLLATERAL_VALUE_IN_LOAN_TOKEN`** The value of the collateral in terms of the loan token
</DocsDefinitionCard>

The collateral value in loan token units is calculated as:

$$
\text{COLLATERAL\_VALUE\_IN\_LOAN\_TOKEN} = \frac{\text{COLLATERAL\_AMOUNT } \times \text{ ORACLE\_PRICE}}{\text{ORACLE\_PRICE\_SCALE}}
$$

<DocsDefinitionCard title="Where:">
  * **`COLLATERAL_AMOUNT`** The amount of collateral assets provided by the user (in token base units)
  * **`ORACLE_PRICE`** The oracle price returned by the oracle of the market (scaled by ORACLE\_PRICE\_SCALE)
  * **`ORACLE_PRICE_SCALE`** A scaling factor of 10^36 used by the protocol for price normalization
</DocsDefinitionCard>

### Liquidation Loan-to-Value (LLTV) [#liquidation-loan-to-value-lltv]

The &#x2A;*Liquidation Loan-to-Value (LLTV)** is the maximum LTV a position can reach before it becomes eligible for liquidation. It is a fixed, immutable parameter for each market, chosen from a governance-approved list at the time of creation.

The rule is simple and absolute:
&#x2A;*If `LTV` ≥ `LLTV`, the position can be liquidated.**

For example, if a market's LLTV is 86%, a user's position is at risk of liquidation as soon as their LTV reaches or exceeds 86%.

### Health Factor [#health-factor]

The Health Factor is another crucial metric that indicates how close a position is to liquidation:

$$
\text{HEALTH\_FACTOR} = \frac{\text{COLLATERAL\_VALUE\_IN\_LOAN\_TOKEN} \times \text{LLTV}}{\text{BORROWED\_AMOUNT}}
$$

<DocsDefinitionCard title="Where:">
  * **`LLTV`** The Liquidation Loan-To-Value threshold set for the market (e.g., 0.86 or 86%), expressed as a WAD (10^18 scaled value, like 860000000000000000)
</DocsDefinitionCard>

A position is healthy when the Health Factor is greater than 1.0. When it falls below 1.0, the position becomes eligible for liquidation.

<Callout type="info">
  * For oracle implementation details, see the [dedicated oracle section](/curate/tutorials-market-v1/deploying-oracle/)
  * WAD represents a common scaling factor in DeFi of 10^18 used for representing decimal numbers in integer arithmetic
</Callout>

<DocsDefinitionCard>
  Let's walk through a concrete example of calculating LTV and Health Factor for a position on Morpho:

  **Given values (with assumptions):**

  * Borrowed amount: 150,000 USDC (150,000,000,000 base units with 6 decimals)
  * Collateral amount: 2 cbBTC (200,000,000 base units with 8 decimals)
  * Oracle price: 1 × 10^39 (means 1 cbBTC = 100000 USDC). This is supposedly the value returned by the price function in the oracle used in the related market
  * Oracle price scale: 10^36
  * LLTV: 86% (expressed as 0.86 × 10^18 or 860,000,000,000,000,000 in WAD units)

  <Steps>
    <Step>
      ### Calculate the collateral value in loan token units [#calculate-the-collateral-value-in-loan-token-units]

      ```typescript
      // All calculations use BigInt (suffixed with 'n') to handle large numbers precisely
      const collateralValueInLoanToken =
        (collateralAmount * oraclePrice) / ORACLE_PRICE_SCALE;
      // = (200,000,000n * 1,000,000,000,000,000,000,000,000,000,000,000,000,000n) / 10n**36n
      // = 200,000,000,000 base units of loan token (USDC)
      ```
    </Step>

    <Step>
      ### Calculate the current LTV [#calculate-the-current-ltv]

      ```typescript
      // Constants
      const WAD = 10n ** 18n; // Standard scaling factor (10^18)

      // Example values
      const borrowedAmount = 150_000_000_000n; // 150 billion units (e.g., USDC with 6 decimals)
      const collateralValueInLoanToken = 200_000_000_000n; // 200 billion units

      /**
       * Current LTV Calculation
       * ----------------------
       *
       * Step 1: Calculate the raw LTV ratio, preserving precision with WAD
       */
      const currentLTV = (borrowedAmount * WAD) / collateralValueInLoanToken;
      // = (150,000,000,000n * 10n**18n) / 200,000,000,000n
      // = 750,000,000,000,000,000n (scaled by WAD, representing 0.75 or 75%)

      /**
       * Option 1: Theoretical Formula
       * ----------------------------
       * In theory, the conversion to percentage is simply:
       */
      // Theoretical formula (doesn't work directly with BigInt)
      // currentLTVPercentage = (currentLTV / WAD) * 100

      // Implementation of theoretical formula (using Number conversion)
      const theoreticalLTVPercentage = (Number(currentLTV) / Number(WAD)) * 100;
      // = 75.0000%

      /**
       * Option 2: Practical Display Implementation
       * ----------------------------------------
       * For precise display with 4 decimal places, we:
       * 1. Scale up by the display factor (percentage * decimal precision)
       * 2. Divide by WAD to normalize
       * 3. Convert to Number and adjust for decimal places
       */
      // Scale factor = 100 (for percentage) * 10000 (for 4 decimal places) = 1,000,000
      const displayScaleFactor = 1_000_000n;
      const currentLTVPercentageScaled = (currentLTV * displayScaleFactor) / WAD;
      // = 750_000n (represents 75.0000%)

      // Convert the scaled BigInt result to a human-readable number
      const displayLTVPercentage = Number(currentLTVPercentageScaled) / 10000;
      // = 75.0000% (when displayed with 4 decimal places)
      ```
    </Step>

    <Step>
      ### Calculate the health factor [#calculate-the-health-factor]

      ```typescript
      // Since LLTV is stored as a WAD, we need to account for scaling
      const healthFactor = (collateralValueInLoanToken * lltv) / borrowedAmount;
      // = (200,000,000,000,000n * 860,000,000,000,000,000n) / 150,000,000,000n
      // = 1,146,666,666,666,666,666 (scaled by WAD)

      // Convert to decimal
      const healthFactorDisplay = Number(healthFactor) / Number(WAD);
      // = 1.1467 (when converted to a human-readable decimal)
      ```

      Since the Health Factor is greater than 1.0 (1.1467), this position is healthy and has a safety margin before liquidation could occur.
    </Step>
  </Steps>

  #### Summary of Position: [#summary-of-position]

  * Current LTV: 75.00%
  * Max LTV (LLTV): 86.00%
  * Health Factor: 1.1467
  * Status: Healthy
  * Liquidation Buffer: 11.00% (difference between current LTV and max LTV)

  This shows a position with an LTV of 75%, which is below the LLTV threshold of 86%. The Health Factor of 1.1467 confirms that the position is healthy with a 11% safety margin before liquidation.
</DocsDefinitionCard>

<Callout type="info">
  * For oracle implementation details, see the [dedicated oracle section](/curate/tutorials-market-v1/deploying-oracle/)
  * For examples of LTV calculations in Solidity, refer to [this code](https://github.com/morpho-org/morpho-blue/blob/12b8a453643d5ef9d55abd88b9f8cfa866882aa5/src/Morpho.sol#L532-L536)
</Callout>

## The Role of Oracles [#the-role-of-oracles]

The accuracy of LTV and Health Factor calculations depends on the **Oracle Price**.

* **Dynamic Pricing:** The oracle provides the real-time exchange rate between the collateral and loan assets. This price is the most dynamic variable in the health calculation.
* **Oracle Complexity:** The oracle for a market might not be a single price feed. It could be a combination of feeds (e.g., `wstETH -> stETH` and `stETH -> ETH`) or rely on other onchain data.
* **Risk Exposure:** The reliability of your LTV and Health Factor display is a direct reflection of the oracle's reliability. Any latency, inaccuracy, or manipulation of the oracle's price can directly impact user positions.

When displaying market information, it is crucial to also provide transparency about the oracle being used.

## Integration Best Practices [#integration-best-practices]

For any application with a borrow interface, a primary goal should be to help users avoid liquidation.

1. **Display Health Factor Prominently:** This should be the most visible metric on any position management dashboard. Use visual aids like colors (green, yellow, red) or progress bars to indicate safety levels.

2. **Clearly State the LLTV:** Users must know the exact "point of no return" for their position. Display the market's `LLTV` alongside the user's current `LTV`.

3. **Implement Proactive Alerts:** When a user's Health Factor drops below a certain safe threshold (e.g., `1.1`), trigger notifications in your UI or via other channels to prompt them to add more collateral or repay part of their loan.

4. **Incorporate Safety Buffers:** Do not allow users to borrow the maximum amount that would place their Health Factor exactly at `1.0`. Your interface should enforce a safety margin, for example, by limiting borrows to a Health Factor of `1.05` or higher.

5. **Simulate Transactions:** Before submitting a `borrow` or `withdrawCollateral` transaction, simulate its effect on the user's Health Factor. Show the user what their new Health Factor will be *before* they sign the transaction.

By following these best practices, you can build a borrow experience that is not only functional but also safe and transparent for your users.

**Next Up:*&#x2A; Learn what happens when the Health Factor drops below 1.0 in the &#x2A;*[Liquidation concept page](/learn/concepts/liquidation/)**.