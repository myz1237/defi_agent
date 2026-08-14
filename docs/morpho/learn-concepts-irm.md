# Interest Rate Model

Source: https://docs.morpho.org/learn/concepts/irm



<figure>
  <ZoomableImage src="/img/homepage/concepts/concepts_irm_light.png" alt="Morpho IRM Concept" />
</figure>

Morpho is an Interest Rate Model (IRM) agnostic protocol, meaning it can support any interest rate model for its markets. In Morpho, the interest borrowers pay in a given market is defined by the IRM chosen at market creation among a governance-approved set.

The only IRM that has been governance-approved is the [AdaptiveCurveIRM](#the-adaptivecurveirm), which is described in more detail later in this page.

## Understanding Borrow and Supply APY [#understanding-borrow-and-supply-apy]

The &#x2A;*Annualized Percentage Yield (APY)** is a critical metric that standardizes interest rates over a one-year period by accounting for compounding. In the context of lending protocols, two key APYs are:

* **Borrow APY:** This reflects the effective annual interest cost that borrowers incur. It is derived from the instantaneous interest rate provided by the chosen Interest Rate Model (IRM). Essentially, the Borrow APY tells borrowers how much they will pay on an annual basis for borrowing assets.

* **Supply APY:** This indicates the effective annual yield that lenders receive on their supplied assets. It is calculated by adjusting the Borrow APY based on the market's utilization rate and any applicable fees. The Supply APY, therefore, not only factors in the raw interest rate but also considers the portion of the rate that is passed on to suppliers after accounting for the market's fee (currently no fees are activated thus the fee equals).

### How Are These APYs Calculated? [#how-are-these-apys-calculated]

<Steps>
  <Step>
    ### Borrow APY Calculation [#borrow-apy-calculation]

    The Borrow APY is obtained by compounding the per-second borrow rate over the entire year. The formula is:

    $$
    \text{borrowAPY} = \left(e^{\left(\text{borrowRate} \times \text{secondsPerYear}\right)} - 1\right)
    $$

    Here, `borrowRate` is the rate provided by the IRM and `secondsPerYear` equals 31,536,000.
  </Step>

  <Step>
    ### Supply APY Calculation [#supply-apy-calculation]

    The Supply APY is obtained by adjusting the Borrow APY like this:

    $$
    \text{supplyAPY} = \text{borrowAPY} \times \text{utilization} \times (1 - \text{fee})
    $$

    Where:

    * **Utilization:** Is the ratio of the total borrowed assets to the total supplied assets.
    * **Fee:** The market's fee determined by governance - currently no fees are applied. (Scaled by [WAD: 1e18](https://github.com/morpho-org/morpho-blue/blob/main/src/interfaces/IMorpho.sol#L94C36-L94C50))
  </Step>
</Steps>

<Callout type="info">
  <Accordions type="single">
    <Accordion title="Borrow and Supply APY Implementation Example">
      Below is a basic typescript snippet showcasing the rate calculus with a rate returned by the IRM of `1512768697`

      ```typescript
      /**
       * Calculate borrow APY using the exponential formula: exp(rate * seconds) - 1
       * Where:
       * - rate is the interest rate per second (in Wei with 18 decimals)
       * - seconds is the number of seconds (typically for a year: 31536000)
       *
       * @param ratePerSecond Interest rate per second in Wei (18 decimals)
       * @param seconds Number of seconds (typically a year: 31536000)
       * @returns The borrow APY as a decimal (e.g., 0.0489 for 4.89%)
       */
      function calculateBorrowRate(ratePerSecond: string, seconds: number): number {
        // Convert rate to a number with 18 decimal precision
        const rate = Number(ratePerSecond) / 1e18;

        // Calculate exp(rate * seconds) - 1
        const result = Math.exp(rate * seconds) - 1;

        return result;
      }

      /**
       * Calculate supply APY based on borrow APY, utilization, and fee
       * Formula: supplyAPY = borrowAPY * utilization * (1 - fee)
       *
       * @param borrowAPY The calculated borrow APY as a decimal (e.g., 0.0489 for 4.89%)
       * @param utilization The utilization rate as a decimal (e.g., 0.8 for 80%)
       * @param fee The fee rate in Wei (18 decimals, e.g., "0" for no fee)
       * @returns The supply APY as a decimal (e.g., 0.0416 for 4.16%)
       */
      function calculateSupplyAPY(
        borrowAPY: number,
        utilization: number,
        fee: string
      ): number {
        // Convert fee from Wei to decimal (1e18 denominator)
        const feeRate = Number(fee) / 1e18;

        // Calculate supply APY using the formula: borrowAPY * utilization * (1 - fee)
        return borrowAPY * utilization * (1 - feeRate);
      }

      // Shared example values
      const secondsInYear = 31536000;
      const ratePerSecond = "1512768697"; // Rate per second in Wei (18 decimals)
      const utilization = 0.85; // 85% utilization
      const fee = "0"; // No fee (0 in Wei / 18 decimals)

      // Calculate borrow APY
      const borrowAPY = calculateBorrowRate(ratePerSecond, secondsInYear);

      // Calculate supply APY
      const supplyAPY = calculateSupplyAPY(borrowAPY, utilization, fee);

      // Display results
      console.log(`Borrow APY: ${(borrowAPY * 100).toFixed(2)}%`);
      console.log(
        `Supply APY: ${(supplyAPY * 100).toFixed(2)}% at ${(
          utilization * 100
        ).toFixed(0)}% utilization with ${(Number(fee) / 1e18) * 100}% fee`
      );
      ```

      The output here is:

      ```
      Borrow APY: 4.89%
      Supply APY: 4.15% at 85% utilization with 0% fee
      ```
    </Accordion>
  </Accordions>
</Callout>

### Resources [#resources]

For a deeper dive into the mechanics and the code behind these calculations, refer to the following resources:

* [**Interest Rate Model Repository**](https://github.com/morpho-org/morpho-blue-irm): Explore the implementation and the smart contracts that power the IRM.
* [**IRM Interface Documentation**](https://github.com/morpho-org/morpho-blue/blob/main/src/interfaces/IIrm.sol): Review the interface definitions and understand how different IRMs integrate into the system.
* [**Introducing the AdaptiveCurveIRM**](https://morpho.org/blog/introducing-the-adaptivecurveirm-efficient-and-autonomous/) article

This integrated approach ensures that both borrowers and suppliers have a clear understanding of the cost of borrowing and the returns on lending, all derived from a robust and governance-approved interest rate model.

Initially, this set is composed of one immutable IRM, the AdaptiveCurveIRM.

## The AdaptiveCurveIRM [#the-adaptivecurveirm]

### Overview [#overview]

The AdaptiveCurveIRM is engineered to maintain the ratio of borrowed assets over supplied assets, commonly called utilization, close to a target of 90%.

In Morpho, the collateral supplied is not rehypothecated. Removing this systemic risk removes the liquidity constraints imposed by liquidation needs. It enables more efficient markets with higher target utilization of capital and lower penalties for illiquidity, resulting in better rates for both lenders and borrowers.

As with every parameter of a Morpho Market, the IRM address is immutable. This means that neither governance nor market creators can change it at any given time. As such, the AdaptiveCurveIRM is designed to adapt autonomously to market conditions, including changes in interest rates on other platforms and, more broadly, any shifts in supply and demand dynamics.

Its adaptability enables it to perform effectively across any asset, market, and condition, making it highly suitable for Morpho's permissionless market creation.

### How It Works [#how-it-works]

The model can be broken down into two complementary mechanisms:

1. **The Curve Mechanism**
   This mechanism is akin to the interest rate curve in traditional lending pools. It manages short-term utilization effectively, maintaining capital efficiency while avoiding excessively high utilization zones that could lead to liquidity issues.

   <div
     style="{
     display: &#x22;flex&#x22;,
     justifyContent: &#x22;center&#x22;,
     marginTop: &#x22;1em&#x22;,
     marginBottom: &#x22;1em&#x22;,
   }"
   >
     <img src="/img/morpho-blue/curve-mechanism-01.png" alt="Curve Mechanism 1" width="800" />
   </div>

$$
r_{90\%} \text{ is the target rate at utilization target } u_{target}=0.9
$$

<Callout type="info">
  Example with the interest rate currently at 4% at

  $$
  u_{target}=0.9
  $$

  * If utilization rate goes to 100% following a market event, the interest rate will instantly go to 16% in this example (x4)

  * At the opposite, if a market event bring the utilization rate to 0%, the interest rate will instantly go to 1% in this example (/4)
</Callout>

2. **The Adaptive Mechanism**
   This mechanism fine-tunes the curve over time to keep the range of rates in sync with market dynamics. It achieves this by adjusting the value of the target rate, which in turn shifts the entire curve:

   * When utilization exceeds the target, the curve continuously shifts upward. This incentivizes loan repayment and thus decreases utilization.
   * When utilization falls below the target, the curve continuously shifts downward. This incentivizes borrowing and thus increases utilization.

   <div
     style="{
     display: &#x22;flex&#x22;,
     justifyContent: &#x22;center&#x22;,
     marginTop: &#x22;1em&#x22;,
     marginBottom: &#x22;1em&#x22;,
   }"
   >
     <img src="/img/morpho-blue/curve-mechanism-02.png" alt="Curve Mechanism 1" width="800" />
   </div>

   The speed at which the curve adjusts is determined by the distance of current utilization to the target: the further it is, the faster the curve shifts.
   This incremental adjustment of the curve allows for rate exploration, ultimately stabilizing when the interest rate at the target utilization aligns with the market equilibrium.

<Callout type="info">
  Some examples are given below about the target

  $$
  r_{90\%}
  $$

  * If the utilization remains at 45%, it will progressively decrease until it is divided by 2 after 10 days.
  * If the utilization remains at 95%, it will progressively increase until it doubles after 10 days.
  * If the utilization remains at 100%, it will progressively increase until it doubles after 5 days. This is the maximum speed at which it can move.
</Callout>

Here's a video showing how the two mechanisms combine to adjust interest rates:

<VideoPlayer freezeOnEnd="true" src="/img/morpho-blue/adaptive-curve-irm.mp4" />

<br />

For more on the AdaptiveCurveIRM, explore the [technical reference](/get-started/resources/contracts/irm).