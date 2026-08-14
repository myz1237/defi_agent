# Liquidation on Morpho

Source: https://docs.morpho.org/learn/concepts/liquidation



<figure>
  <ZoomableImage src="/img/homepage/concepts/concepts_liquidation_light.png" alt="Morpho Liquidation Concept" />
</figure>

## Overview [#overview]

Liquidation is a critical mechanism in the Morpho protocol that protects lenders' capital by ensuring borrowers maintain healthy collateral positions. Morpho liquidation is built into the protocol core and allows full or partial position liquidation when a borrower's Loan-To-Value (LTV) exceeds the Liquidation Loan-To-Value (LLTV) threshold.

## Understanding Loan-To-Value (LTV) [#understanding-loan-to-value-ltv]

Before exploring liquidation, it's essential to understand how LTV is calculated and what it represents.

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
  * For oracle implementation details, see the [dedicated oracle section](/learn/concepts/oracle/)
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
  * For oracle implementation details, see the [dedicated oracle section](/learn/concepts/oracle/)
  * For examples of LTV calculations in Solidity, refer to [this code](https://github.com/morpho-org/morpho-blue/blob/12b8a453643d5ef9d55abd88b9f8cfa866882aa5/src/Morpho.sol#L532-L536)
</Callout>

## Liquidation Mechanism [#liquidation-mechanism]

Liquidation is the primary defense against borrower defaults and is built directly into the Morpho core contracts.

### When Is a Position Liquidatable? [#when-is-a-position-liquidatable]

A position becomes liquidatable when its LTV exceeds the market's Liquidation Loan-To-Value (LLTV) which can happen due to:

* Collateral value decreasing
* Debt increasing due to accrued interest
* A combination of both factors

<Callout type="info">
  **Example**
  If a borrower provides $100 of collateral in a market with an LLTV of 86%:

  * The position is safe when borrowed value ≤ $86
  * The position becomes liquidatable when borrowed value > $86 (LTV > 86%)
</Callout>

### How Liquidation Works [#how-liquidation-works]

When a position becomes liquidatable, any external party (a liquidator) can repay part or all of the borrower's debt in exchange for an equivalent amount of collateral plus a liquidation bonus.

#### Liquidation Incentive Factor (LIF) [#liquidation-incentive-factor-lif]

The liquidation bonus is determined by the Liquidation Incentive Factor (LIF), which depends on the market's LLTV:

$$
\text{LIF} = \min(M, \frac{1}{\beta*\text{LLTV}+(1-\beta)}), \text{ with } \beta = 0.3 \text{ and } M= 1.15.
$$

<div
  style="{
  display: &#x22;flex&#x22;,
  flexDirection: &#x22;column&#x22;,
  justifyContent: &#x22;center&#x22;,
  alignItems: &#x22;center&#x22;,
  marginBottom: &#x22;1em&#x22;,
}"
>
  <img src="/img/morpho-blue/lif-lltv.png" alt="LIF vs LLTV graph" style="{ maxWidth: &#x22;75%&#x22; }" />

  <p>
    Liquidation Incentive Factor in relation to the Liquidation Loan-To-Value
  </p>
</div>

<Callout type="info">
  * The entire LIF goes to the liquidator; Morpho protocol doesn't take a fee
  * For an 86% LLTV market, the LIF is approximately 1.05 (5% bonus)
</Callout>

### Liquidation Step-by-Step [#liquidation-step-by-step]

<Steps>
  <Step>
    ### Initial Position [#initial-position]

    A borrower deposits $100k of collateral in a market with LLTV = 86% and borrows $70k. Due to accrued interest (an example could be provided with only collateral price depreciation), the loan value increases to $86.01k.

    * Position status: LTV = 86.01% > LLTV (86%) → **Liquidatable**
  </Step>

  <Step>
    ### Liquidation Process [#liquidation-process]

    * Liquidator identifies the unhealthy position
    * Liquidator repays the $86.01k debt
    * LIF calculation: 1.05 (for 86% LLTV market)
    * Seized collateral: $86.01k × 1.05 = $90.31k
  </Step>

  <Step>
    ### After Liquidation [#after-liquidation]

    * Borrower: Debt cleared, retains $9.69k of collateral
    * Liquidator: Spent $86.01k, received $90.31k in collateral
    * Profit for liquidator: $4.3k minus gas fees and any swap costs
  </Step>

  <Step>
    ### Practical Consideration [#practical-consideration]

    For this liquidation to be profitable, the liquidator must ensure:
    $4.3k > (Gas fees + potential swap fees + potential price slippage costs)
  </Step>
</Steps>

### Key Features of Liquidation [#key-features-of-liquidation]

* **Liquidation Amount**: Liquidators can repay up to 100% of the borrower's debt in a single transaction
* **Trigger**: Only activates when LTV > LLTV
* **Incentive**: Fixed LIF based on the market's LLTV
* **Borrower Impact**: Potentially significant one-time liquidation
* **Implementation**: Built into the Morpho core contract

## Bad Debt Consideration [#bad-debt-consideration]

### Morpho Vaults V2 - Loss Socialization [#morpho-vaults-v2---loss-socialization]

Morpho Vault V2 implements an automatic loss socialization mechanism where losses - including bad debt from underlying adapters - are detected and distributed proportionally across all shareholders through share price depreciation.

#### How It Works [#how-it-works]

1. **Loss Detection:** Each adapter reports the actual current value of its investments via a `realAssets()` function. When bad debt occurs in an underlying adapter, this reported value automatically decreases.

2. **Loss Realization:** During interest accrual, the vault compares the reported real asset value to its internally tracked total. If `realAssets` has dropped below the previously recorded `totalAssets`, the vault updates its accounting downward to reflect the loss.

3. **Automatic Socialization:** Share value is determined via `convertToAssets()`, which computes `shares × (totalAssets + 1) / (totalSupply + virtualShares)`. When `totalAssets` decreases, every share redeems for fewer assets. No shares are burned - all shareholders absorb the loss proportionally.

#### Important Considerations [#important-considerations]

* **Management fee** continue to accrue even during loss periods.
* **Flash loan protection:** The vault includes safeguards against share price manipulation around loss realization events, as losses are only accounted for once per transaction.

<Callout type="warn">
  **Legacy Morpho Vault V1.1 caveat:** Morpho Vaults V1 are now legacy. However, Morpho Vault V2 deployments that still use a `MorphoVaultV1Adapter` to allocate into a legacy Morpho Vault V1.1 should be aware that Morpho Vaults V1.1 do not realize bad debt internally. As a result, the corresponding losses from that allocation will not be reflected in the V2 vault's share price until the V1.1 vault itself accounts for them.
</Callout>

### Legacy - Morpho Vaults V1 [#legacy---morpho-vaults-v1]

Morpho Vault V1 has different mechanisms for accounting for bad debts depending on the vault version.

#### Morpho Vaults V1.0 - Bad Debt Realization (Legacy) [#morpho-vaults-v10---bad-debt-realization-legacy]

The Morpho Vaults created with [the MetaMorpho FactoryV1.0](https://github.com/morpho-org/metamorpho) have a mechanism to account for and realize bad debt in the event it arises.

Typically, in other lending pool designs, accrued bad debt remains in the market forever until manual intervention to pay down the bad debt. If small enough, the markets can continue functioning. If it is significant, the market becomes unusable.

Morpho Vaults V1.0 treat bad debt differently. When a liquidation leaves an account with some remaining debt, and without collateral to cover it, the loss is realized and shared proportionally between all lenders.

As bad debt is realized at the time it occurs, a market can be used in perpetuity.

#### Morpho Vaults V1.1 - No Bad Debt Realization (Legacy) [#morpho-vaults-v11---no-bad-debt-realization-legacy]

The Morpho Vaults created with [the MetaMorpho Factory V1.1](https://github.com/morpho-org/metamorpho-v1.1) have a different mechanism as they do not realize bad debt and behave as other lending pools with accrued debt remaining in the market forever until manual intervention to pay down the bad debt.

## Liquidation FAQ [#liquidation-faq]

#### At what price are liquidations done? [#at-what-price-are-liquidations-done]

Liquidations occur at the current oracle price when a position's LTV exceeds the market's LLTV. The oracle price determines both when a position becomes liquidatable and the exchange rate during the liquidation process. The liquidator receives collateral valued at debt amount × LIF according to this oracle price, regardless of market conditions or price volatility elsewhere.

#### What happens if the collateral price continues to fall? [#what-happens-if-the-collateral-price-continues-to-fall]

If the collateral price continues to fall after a position becomes liquidatable:

* The position becomes increasingly attractive for liquidators as they can seize a larger percentage of the collateral relative to its real market value
* Liquidators are incentivized to act quickly to capture this value
* The protocol's design encourages prompt liquidations to minimize systemic risk
* There is no price floor - the position remains liquidatable until someone repays the debt

#### What happens if the price recovers before liquidation happens? [#what-happens-if-the-price-recovers-before-liquidation-happens]

If the collateral price recovers sufficiently before liquidation occurs:

* The position's LTV may drop below the LLTV threshold
* The position will no longer be liquidatable
* The borrower retains their full collateral and remains responsible for their debt
* This scenario highlights why borrowers should maintain a safety buffer below the LLTV

#### How do competing liquidators interact? Is it first-come-first-served? [#how-do-competing-liquidators-interact-is-it-first-come-first-served]

Yes, liquidations operate on a first-come-first-served basis:

* The first transaction that successfully executes the liquidation claims the opportunity
* There is no auction or bidding mechanism
* In competitive environments, this can lead to MEV (Maximal Extractable Value) opportunities and potential gas price wars
* Advanced liquidators may use flashbots or other private transaction methods to secure their liquidation

#### Is there partial liquidation? [#is-there-partial-liquidation]

Yes. Liquidators can choose to liquidate any amount of the borrower's debt up to the full amount. This allows for optimizing gas costs against liquidation profits, especially for large positions where full liquidation might cause significant market impact.

#### How are liquidations guaranteed for assets like cbBTC/stETH? [#how-are-liquidations-guaranteed-for-assets-like-cbbtcsteth]

Liquidations in Morpho are driven by economic incentives rather than absolute guarantees. The protocol doesn't perform liquidations itself; instead, when a position becomes unhealthy, it becomes eligible for liquidation by external actors. The system is designed with incentives (via the Liquidation Incentive Factor) to make liquidations profitable enough that third parties will consistently execute them.

For assets like cbBTC or stETH, the key factor is whether the market's specific LIF provides enough incentive to outweigh potential costs associated with liquidating that particular collateral type. The ability to perform partial liquidations also helps with larger positions, as they can be liquidated incrementally by multiple parties or in several steps.

#### Who are the liquidators and what tools do they use? [#who-are-the-liquidators-and-what-tools-do-they-use]

Liquidators are permissionless participants in the Morpho ecosystem. Anyone who identifies an eligible position and has the necessary assets can perform a liquidation. The ecosystem includes a diverse range of participants, from sophisticated teams running automated bots to individuals.

At a basic level, performing a liquidation only requires access to an RPC node and a wallet with sufficient assets. However, competitive liquidators typically utilize automated bots that continuously monitor onchain data (loan positions, oracle prices) to identify and execute liquidations efficiently.

Some liquidators implement swap systems allowing them to seize collateral and repay loans without needing to hold the loan asset beforehand, effectively acting as a liquidity venue. The Morpho ecosystem also includes open-source liquidation bots that community members can deploy.

## Liquidation Tools [#liquidation-tools]

<Callout type="error">
  Some community members have contributed and provided liquidation bots that could be deployed to liquidate positions.

  * Morpho Association nor authors of these repositories can be held responsible for any losses or damages that may result from the use of this information.
  * Users are advised to conduct their own research and exercise caution when applying any strategies or methods described herein.

  If you are comfortable with these conditions, you can explore the liquidation community section [here](/developers/ecosystem/liquidation-bots/)
</Callout>

***

By understanding liquidation mechanics, users can better manage their risk on Morpho and protect their positions from adverse market movements.