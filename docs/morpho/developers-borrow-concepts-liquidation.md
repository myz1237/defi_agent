# Liquidation

Source: https://docs.morpho.org/developers/borrow/concepts/liquidation



Liquidation is one of the core mechanism in Morpho. It protects lenders' capital by ensuring that undercollateralized loans are repaid, thereby maintaining the solvency of each market. For any developer integrating a borrowing feature, understanding and clearly communicating how liquidation works is paramount.

When a borrower's position becomes too risky, the protocol allows a third party-a **liquidator**-to step in, repay the debt, and seize the borrower's collateral at a discount.

## When Does Liquidation Occur? [#when-does-liquidation-occur]

A position becomes eligible for liquidation the moment its **Health Factor drops to 1 or below**.

As a reminder, this happens when the Loan-to-Value (LTV) of a position meets or exceeds the market's immutable Liquidation Loan-to-Value (LLTV) threshold.

$$
  \text{If} \quad \frac{\text{Debt Value}}{\text{Collateral Value}} \ge \text{LLTV} \quad \implies \quad \text{Position is Liquidatable}
$$

This can be caused by:

* A decrease in the price of the collateral asset.
* An increase in the value of the debt due to accrued interest.

## The Liquidation Process [#the-liquidation-process]

Liquidation on Morpho is a straightforward, economically-driven process. It is not an auction; it's a direct transaction executed by the first liquidator to act.

<Steps>
  <Step>
    ### 1. An Unhealthy Position is Identified [#1-an-unhealthy-position-is-identified]

    A liquidator (typically an automated bot) detects a position where the Health Factor is ≤ 1.
  </Step>

  <Step>
    ### 2. Liquidator Repays the Debt [#2-liquidator-repays-the-debt]

    The liquidator calls the `liquidate` function on the Morpho contract, repaying a portion or all of the borrower's debt using the loan asset.
  </Step>

  <Step>
    ### 3. Liquidator Seizes Collateral at a Discount [#3-liquidator-seizes-collateral-at-a-discount]

    In return for repaying the debt, the liquidator is allowed to seize an equivalent value of the borrower's collateral, plus a bonus. This bonus is the liquidator's incentive and profit.
  </Step>

  <Step>
    ### 4. The Borrower's Position is Updated [#4-the-borrowers-position-is-updated]

    The borrower's debt is reduced or eliminated, and their collateral is reduced by the amount seized.
  </Step>
</Steps>

### The Liquidation Incentive Factor (LIF) [#the-liquidation-incentive-factor-lif]

The "discount" or "bonus" a liquidator receives is determined by the &#x2A;*Liquidation Incentive Factor (LIF)**. This factor is calculated based on the market's LLTV, ensuring that riskier markets (with higher LLTVs) offer a smaller bonus to prevent cascading liquidations.

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
</div>

For a market with an &#x2A;*LLTV of 86%**, the **LIF is approximately 1.05**, meaning the liquidator receives a **5% bonus** on the collateral they seize. This entire incentive goes to the liquidator; the Morpho protocol takes no fee.

### Example: A Liquidation Scenario [#example-a-liquidation-scenario]

* **Initial State*&#x2A;: A user has a position in a market with an LLTV of 86%. Their debt has grown to **$87,000*&#x2A;, while their collateral value has dropped to **$100,000**.
* **Health Check**: The LTV is 87% (`87k / 100k`), which is greater than the 86% LLTV. The position is liquidatable.
* **Liquidation*&#x2A;: A liquidator repays the full **$87,000** debt.
* **Collateral Seized**: The liquidator seizes `$87,000 * 1.05&#x60; (LIF) = **$91,350** worth of the borrower's collateral.
* **Outcome**:
  * **Borrower*&#x2A;: Their debt is cleared, but they lose $91,350 of their $100,000 collateral, incurring a loss of **$4,350**.
  * **Liquidator*&#x2A;: Profits by **$4,350** (minus gas and transaction costs).

### Bad Debt [#bad-debt]

In extreme cases where the collateral's value drops so fast that it becomes less than the debt (`LTV > 100%`), a liquidation might not cover the full loan. The remaining unpaid debt is known as **bad debt**. This represents a loss for lenders in that market. Morpho's design, including its risk-isolated markets and conservative LLTVs, aims to make this a rare event.

## Integration Best Practices for Developers [#integration-best-practices-for-developers]

Your primary goal as an integrator is to help your users avoid liquidation.

1. **Prioritize Health Factor Display:** The Health Factor should be the most prominent metric for any user with an open borrow position. Use clear visual cues (colors, gauges) to communicate risk.

2. **Educate About the "Point of No Return":** Clearly display the market's LLTV and the user's current LTV. The user must understand that crossing the LLTV threshold is the trigger for liquidation.

3. **Implement Proactive Alerts:** Build notifications within your application to warn users when their Health Factor drops to a cautionary level (e.g., below 1.1).

4. **Simulate Transactions:** Before a user confirms a `borrow` or `withdrawCollateral` transaction, show them the resulting Health Factor. This prevents them from unknowingly putting their position at risk.

By treating liquidation as a core part of the user experience, you can build a safer and more trustworthy borrowing platform.