# Interest Rates

Source: https://docs.morpho.org/developers/borrow/concepts/interest-rates



Understanding how interest rates are determined and how they affect a borrower's position is fundamental to building a safe and transparent borrow integration. In Morpho, the interest a borrower pays is dictated by the market's &#x2A;*Interest Rate Model (IRM)**.

## The Role of the Interest Rate Model (IRM) [#the-role-of-the-interest-rate-model-irm]

Each Morpho Market is created with a specific, immutable IRM. This smart contract contains the logic that dynamically calculates the borrow interest rate based on market conditions, primarily the **utilization rate**.

* **Utilization Rate:** The ratio of total borrowed assets to total supplied assets in a market.
  $$
    \text{Utilization} = \frac{\text{Total Borrows}}{\text{Total Supply}}
  $$

* **Governance-Approved IRMs:** Only IRMs that have been approved by Morpho Governance can be used to create new markets. Currently, the primary model is the `AdaptiveCurveIRM`.

### The AdaptiveCurveIRM [#the-adaptivecurveirm]

The `AdaptiveCurveIRM` is designed to maintain market utilization around a target of &#x2A;*90%**.

* **When utilization \< 90%:** The borrow rate gradually decreases to incentivize more borrowing.
* **When utilization > 90%:** The borrow rate rapidly increases to encourage repayments and attract more supply.

This mechanism ensures that markets remain capital-efficient while having enough liquidity for withdrawals.

<Callout type="info">
  For a deeper dive into the mathematical formulas and adaptive mechanics, see the &#x2A;*[IRM Concept Page](/learn/concepts/irm/)**.
</Callout>

## How Interest Accrues on Debt [#how-interest-accrues-on-debt]

For a borrower, the most important takeaway is that **interest is constantly accruing**, increasing their total debt over time. This directly impacts their position's health.

The process is as follows:

<Steps>
  <Step>
    ### 1. Rate Calculation [#1-rate-calculation]

    The IRM calculates the instantaneous `borrowRate` based on the market's current utilization.
  </Step>

  <Step>
    ### 2. Interest Accrual [#2-interest-accrual]

    This rate is applied to the borrower's debt continuously. The amount of interest accrued increases the `totalBorrowAssets` in the market and, proportionally, the asset value of each borrower's `borrowShares`.
  </Step>

  <Step>
    ### 3. Impact on Health Factor [#3-impact-on-health-factor]

    As the debt value increases due to accrued interest, the user's **LTV rises** and their **Health Factor falls**, even if collateral and asset prices remain stable.
  </Step>
</Steps>

$$
  \text{Health Factor} = \frac{\text{Collateral Value} \times \text{LLTV}}{\text{Initial Debt} + \text{Accrued Interest}}
$$

This is a critical concept to communicate to users: their position can become riskier over time simply from interest accrual.

## Onchain State and `accrueInterest` [#onchain-state-and-accrueinterest]

The Morpho contract does not update interest for every block to save gas. Instead, interest is calculated and applied only when a market interaction occurs via the `_accrueInterest` internal function. This function is triggered by actions like `borrow`, `repay`, `supply`, and `withdraw`.

**What this means for your integration:**

When you fetch a user's position from the contract, the `totalBorrowAssets` value reflects the state at the *last interaction*. To get the up-to-the-second debt value, you must account for the interest accrued since the `lastUpdate` timestamp.

Jump on the tutorials to learn how to accrue the interests up to the last block.

See the [Get Data Tutorial](/developers/borrow/tutorials/get-data#onchain--sdk-required-for-real-time-accuracy) for a practical example.

## Integration Best Practices [#integration-best-practices]

* **Display Real-Time APY:** Don't just show the instantaneous borrow APY, which can be volatile. Provide users with a time-averaged APY (e.g., 6-hour average) to give a more realistic view of their borrowing costs.
* **Educate Users on Accruing Debt:** Your UI should make it clear that the user's debt amount is continuously increasing and that this affects their Health Factor.
* **Simulate Interest Impact:** When users are opening a position, provide them with projections of how their Health Factor might change over time due to interest accrual, especially in volatile rate environments.

By correctly implementing and displaying interest rate mechanics, you empower users to manage their borrow positions effectively and safely.