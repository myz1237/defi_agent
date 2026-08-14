> ## Documentation Index
> Fetch the complete documentation index at: https://docs.li.fi/llms.txt
> Use this file to discover all available pages before exploring further.

# Debugging Failed Transactions

> Learn how to diagnose and fix reverted on-chain transactions using Blocksec Explorer and Tenderly

Learn how to debug reverted transactions using trace analysis tools. This guide covers common failure patterns and their fixes based on real production cases.

## Prerequisites

Before you begin, you need:

* The **transaction hash** of the failed transaction
* Access to a trace analysis tool

<CardGroup cols={2}>
  <Card title="Blocksec Explorer" icon="magnifying-glass" href="https://app.blocksec.com/explorer">
    View detailed call traces and analyze transactions
  </Card>

  <Card title="Tenderly Debugger" icon="bug" href="https://tenderly.co/">
    Simulate and debug transactions step-by-step
  </Card>
</CardGroup>

***

## Core Debugging Workflow

Follow these steps to diagnose most transaction failures.

<Steps>
  <Step title="Find the Revert Location">
    Open the transaction in Blocksec or Tenderly and identify:

    * The **top-level revert reason** (if available)
    * The **first revert** in the call tree (this is often the actual root cause)
    * The **contract or call before the revert** (this is the failing action)

    <Tip>
      Trace tools sometimes show multiple errors. When the UI summary conflicts with the raw trace, trust the raw trace.
    </Tip>
  </Step>

  <Step title="Classify the Failure">
    Most reverts fall into these categories:

    | Category               | Common Indicators                                         |
    | ---------------------- | --------------------------------------------------------- |
    | Out of gas             | Trace ends abruptly, OOG error                            |
    | Insufficient allowance | `transfer amount exceeds allowance`                       |
    | Insufficient balance   | `insufficient balance`, `transfer amount exceeds balance` |
    | Missing msg.value      | `insufficient balance for transfer` on native token       |
    | Slippage exceeded      | Min output checks fail                                    |
    | Oracle issues          | `StalePrice`, bad feed errors                             |
    | Deadline expired       | `EXPIRED`, `Transaction too old`                          |
    | Token restrictions     | Transfer blocked, tax fees, blacklist                     |

    Once you identify the category, the fix becomes clear.
  </Step>

  <Step title="Compare Expected vs Actual Inputs">
    Aggregator and router failures often stem from input mismatches:

    * `gasLimit` on-chain vs `gasLimit` from `/quote` or `/stepTransaction`
    * Approval amount vs actual spend amount
    * `msg.value` sent vs `msg.value` required
    * `minAmountOut` vs actual output at execution
    * Token address or price feed ID errors
  </Step>

  <Step title="Reproduce and Test">
    Simulate the failed call with identical calldata and state. Then change one variable at a time:

    * Increase `gasLimit`
    * Add or adjust `msg.value`
    * Relax slippage parameters

    <Note>
      If changing one variable makes the simulation succeed, you have found the root cause.
    </Note>
  </Step>
</Steps>

***

## Common Failure Modes

<AccordionGroup>
  <Accordion title="A) Out of Gas" icon="gas-pump">
    ### Symptom

    The trace ends abruptly or shows an out-of-gas (OOG) error.

    ### How to Confirm

    1. Check the transaction's `gasLimit`
    2. Look for OOG in the revert reason
    3. Re-simulate with a higher `gasLimit` (use the value from the quote API)

    ### Root Cause

    The transaction used a lower `gasLimit` than the quote recommended. Wallets or relayers sometimes override gas settings.

    ### Fix

    * Use the **exact `gasLimit`** from the quote response
    * Add a 10–20% safety buffer if your product allows it
    * Verify that wallets and relayers do not clamp gas values

    ### Example

    The API returned sufficient `gasLimit`, but the on-chain transaction reverted. Re-simulating with the correct `gasLimit` succeeded.

    * [Failed transaction](https://app.blocksec.com/explorer/tx/base/0xdb8adb7526ab1372f3e252ddc128c3e039bd29bb91567f5f3821b7c665b16dd9?line=302)
    * [Successful simulation](https://app.blocksec.com/explorer/tx/base/0x9c0d91d0f2de0250b75f59276b879b5309f3f4d6eaa688b943fd11c39c418f45?event=simulation\&timestamp=1767602633035\&type=0)
  </Accordion>

  <Accordion title="B) Insufficient Allowance" icon="ban">
    ### Symptom

    Revert message: `transfer amount exceeds allowance`

    ### How to Confirm

    1. Find the `transferFrom(...)` call in the trace
    2. Identify which spender is pulling funds
    3. Check `allowance(owner, spender)` at the execution block

    ### Root Cause

    The user either did not approve, approved the wrong spender, or approved less than the required amount. A previous transaction may have consumed the allowance.

    ### Fix

    * Prompt an approval for the correct token and spender
    * Consider infinite approval vs exact approval tradeoffs

    ### Example

    [Transaction reverted due to insufficient allowance](https://app.blocksec.com/explorer/tx/base/0xa24e8a320ed5c7e9b5daa5d6c5e0616b0b4789cc6e68b2872b24970d0aca733c?line=11)
  </Accordion>

  <Accordion title="C) Missing msg.value" icon="coins">
    ### Symptom

    Errors such as:

    * `insufficient balance for transfer`
    * Native value forwarding fails

    ### How to Confirm

    1. Check the transaction's `msg.value` in Tenderly
    2. Find where the router forwards ETH in the trace
    3. Look for balance failures at that point

    ### Root Cause

    The route requires native tokens (for fees, bridged gas, or protocol payments), but the transaction sent `value=0`.

    ### Fix

    * Include the `msg.value` returned by the API
    * Verify that relayers and wallets do not drop the value field

    ### Example

    The transaction failed because `msg.value` was missing despite the API returning a non-zero value.

    [View in Tenderly](https://dashboard.tenderly.co/shared/simulation/b444cc7e-5deb-4ac6-a3f4-fdeb8fe7eded/debugger?trace=0.1.2)
  </Accordion>

  <Accordion title="D) Stale Oracle Price" icon="clock-rotate-left">
    ### Symptom

    Revert message: `PythErrors.StalePrice()`

    ### How to Confirm

    Look for `getPriceNoOlderThan(..., age=N)` reverting in the trace.

    ### Root Cause

    The oracle data is too old, or the pool uses an incorrect feed ID that is not being updated.

    ### Fix

    Contact [LI.FI support](https://lifihelp.zendesk.com/hc/en-us) to report the issue.

    ### Example

    `PythErrors.StalePrice()` occurred because a pool used an incorrect feed ID.

    [View in Tenderly](https://dashboard.tenderly.co/shared/simulation/05f5aaf2-3946-42ed-b9f6-45fd40b78e2d/debugger?trace=0.4.3.0.2.0.0.1.6.7.1.5.0.1.1.2.2.0.1.0.2)
  </Accordion>

  <Accordion title="E) Insufficient Token Balance" icon="wallet">
    ### Symptom

    Revert message: `insufficient balance` or `transfer amount exceeds balance`

    ### How to Confirm

    1. Find the token transfer in the trace
    2. Identify the "from" address
    3. Check `balanceOf(from)` at execution time

    ### Root Cause

    The user's balance changed between quote and execution. Fee-on-transfer or rebasing tokens can cause unexpected balance changes.

    ### Fix

    * Re-quote and verify balances immediately before sending
    * For fee-on-transfer tokens, contact LI.FI support to add the token to the deny list

    ### Example

    [Transaction reverted due to insufficient balance](https://app.blocksec.com/phalcon/explorer/tx/eth/0xefb4dc79dc72b1df1d13edd2a4727594b1a1a8aff3c5ca6792a0ce1068f87d88?line=6)
  </Accordion>

  <Accordion title="F) Slippage Exceeded" icon="chart-line-down">
    ### Symptom

    Revert related to minimum output or slippage checks (exact message varies by DEX).

    ### How to Confirm

    Find the swap step and compare:

    * `amountOutMin` or `minReturnAmount`
    * Actual computed `amountOut`

    If `amountOut < minReturnAmount`, the transaction reverts.

    ### Root Cause

    Price movement, MEV extraction, volatile pools, low liquidity, or stale quotes.

    ### Fix

    * Re-quote and execute within 60–90 seconds of quoting (most common cause is a stale quote)
    * If fresh quotes still fail, increase slippage tolerance for **diagnostic purposes only** (15–25% for volatile or new tokens)
    * For unavoidable high slippage, use a private or MEV-protected RPC endpoint

    <Warning>
      Do not use high slippage values as a production default. This creates a wide window for [sandwich attacks](https://ethereum.org/en/developers/docs/mev/#mev-examples-sandwich-trading) where MEV bots can extract value from users. Only use these values for one-off debugging.
    </Warning>

    ### Example

    * [Slippage failure (Tenderly)](https://www.tdly.co/tx/0xd695011e11cdf38e92edf5c872a1bab4f011e90a493b5696e2a0092460268ccc)
    * [Slippage failure (Blocksec)](https://app.blocksec.com/phalcon/explorer/tx/eth/0x9b613a583daa4a6a46e4bacbe13bb571d4a7e897a5b0b0ca44b3260856fc2ef4?line=2)
  </Accordion>

  <Accordion title="G) Token Transfer Restriction" icon="triangle-exclamation">
    ### Symptom

    The final swap step fails with `SafeERC20: low-level call failed`.

    ### How to Confirm

    In the trace, look for:

    1. A `transferFrom` call that reverts
    2. A nested external call that fails (often to a tax wallet or fee handler)
    3. The error bubbling up as `SafeERC20: low-level call failed`

    ### Root Cause

    Some tokens have custom transfer logic that fails under certain conditions. For example, tokens with sell taxes may call external contracts that reject ETH or revert unexpectedly.

    ### Fix

    * Treat the token as incompatible for sell routes
    * Report to [LI.FI support](https://lifihelp.zendesk.com/hc/en-us) for addition to the token deny list

    <Tip>
      Use token risk scanners like [honeypot.is](https://honeypot.is) or [GoPlus](https://gopluslabs.io/) to check for honeypot flags, sell restrictions, or abnormal taxes.
    </Tip>

    ### Example

    The router failed to transfer tokens because the token's tax wallet rejected ETH.

    [View in Blocksec](https://app.blocksec.com/phalcon/explorer/tx/eth/0xca85cc530034c4fec9b0ee6831607a947fa8032e7919881d5fd3101c1bd5cd92?line=75)
  </Accordion>

  <Accordion title="H) Broken Pool (Math Failure)" icon="infinity">
    ### Symptom

    Revert inside pool math, such as Curve's `get_D` failing to converge after 255 iterations.

    ### How to Confirm

    The trace shows a revert in pool math functions (`get_D`, invariant computation) with a `raise` statement.

    ### Root Cause

    The pool is broken, often due to a compromised token causing extreme imbalance or invalid state.

    ### Fix

    Contact [LI.FI support](https://lifihelp.zendesk.com/hc/en-us) to blacklist the pool.

    ### Example

    A Curve pool's `get_D` function failed to converge. The Curve team confirmed the pool was broken.

    [View in Tenderly](https://dashboard.tenderly.co/tx/0x18505dfe414ab0e347d4d174217737c41d5b84db3bd6a6af3af6f0cff37b3367?trace=0.1.1.9.2.0.5.0.9.1.0)
  </Accordion>

  <Accordion title="I) Reentrancy Lock (UniswapV2 LOCKED)" icon="lock">
    ### Symptom

    Revert message: `UniswapV2: LOCKED`

    ### How to Confirm

    In the trace:

    1. The Uniswap V2 pair transfers a token
    2. The token's transfer logic calls back into the same pair
    3. The pair's reentrancy lock triggers

    ### Root Cause

    A token with callback or fee-swap logic re-enters the pair during transfer. This often happens with misconfigured fee-on-transfer tokens.

    ### Fix

    Contact [LI.FI support](https://lifihelp.zendesk.com/hc/en-us) to blacklist the pool.

    ### Example

    Swaps involving WeightedIndex reverted with `UniswapV2: LOCKED`. KyberSwap blacklisted the affected pool.

    [View in Tenderly](https://dashboard.tenderly.co/shared/simulation/c5b100d0-067d-483a-9184-0880f709a382/debugger?trace=0.4.2.0.2.2.0.1.6.7.1.5.3.5.0.0.0.1.2.1.7.3.3.6.1)
  </Accordion>

  <Accordion title="J) Fee-on-Transfer Token Failure" icon="percent">
    ### Symptom

    Revert due to insufficient balance mid-route, even though the user had enough tokens initially.

    ### How to Confirm

    The trace shows:

    1. An earlier hop receives less tokens than expected
    2. A later hop tries to transfer the originally calculated amount
    3. The balance check fails

    ### Root Cause

    Fee-on-transfer (FoT) or deflationary tokens take a fee during transfer. The route assumes exact amounts, but the actual received amount is less than calculated.

    ### Fix

    Contact [LI.FI support](https://lifihelp.zendesk.com/hc/en-us) to add the token to the deny list.

    ### Example

    fBOMB failed with `Max20: insufficient balance` because its deflationary mechanism broke the route's exact calculations.

    * [View in Tenderly](https://dashboard.tenderly.co/shared/simulation/0cb72ac2-1565-4d10-9919-11b584f07f4f?trace=0.4.2.0.5.1.0.1.2)
    * [View token code](https://berascan.com/address/0xfab311fe3e3be4bb3fed77257ee294fb22fa888b#code#F1#L133)
  </Accordion>

  <Accordion title="K) DEX Reentrancy Protection" icon="shield-halved">
    ### Symptom

    Revert caused by a pool-level reentrancy lock, especially with fee-on-transfer tokens.

    ### How to Confirm

    The trace shows a revert at the pool with reentrancy guard behavior, similar to "LOCKED" but protocol-specific.

    ### Root Cause

    Newer DEXs add reentrancy protections that conflict with fee-on-transfer or callback tokens.

    ### Fix

    Contact [LI.FI support](https://lifihelp.zendesk.com/hc/en-us) to blacklist the pool.

    ### Example

    Kodiak v2 pools added reentrancy locks that caused fee-on-transfer tokens to revert.

    [View in Tenderly](https://dashboard.tenderly.co/shared/simulation/8671ce2c-c34e-436d-8496-3bce168dea08?trace=0.4.2.0.2.8.0.1.6.7.1.7.3.5.0.0.1.2.1.7.3.3.6.1)
  </Accordion>

  <Accordion title="L) Expired Deadline" icon="hourglass-end">
    ### Symptom

    Revert messages such as:

    * `Transaction too old`
    * `EXPIRED`
    * `SwapRouter: EXPIRED`

    ### How to Confirm

    1. Find the encoded deadline in the calldata (usually a 32-byte word)
    2. Convert the hex value to Unix time
    3. Compare to the block timestamp when the transaction was mined

    If `block_timestamp > deadline`, the router rejects the transaction.

    **Example calculation:**

    * Deadline: `0x6951e2e0` = 1,766,974,176
    * Block timestamp: 1,766,975,579
    * Delta: 1,403 seconds (\~23 minutes late)

    [View VM trace](https://etherscan.io/vmtrace?txhash=0x15735cdc5b7576ff6059a7337c8d48767a56210ac88cce26f6a8d470d2c791b1\&type=gethtrace2)

    ### Root Cause

    The transaction was submitted too late due to slow signing, mempool congestion, low gas price, or relayer delays.

    ### Fix

    * Get a fresh quote and submit immediately
    * Increase gas price for stuck transactions
    * Do not reuse old calldata

    <Warning>
      Late execution often means the market has moved. Even without an explicit deadline revert, stale quotes frequently fail due to slippage. Always re-quote.
    </Warning>
  </Accordion>
</AccordionGroup>

***

## Quick Decision Checklist

Follow these steps when debugging a failed transaction:

<Steps>
  <Step title="Find the First Revert">
    Look at the call tree, not just the UI headline. The first revert is usually the root cause.
  </Step>

  <Step title="Identify the Category">
    | Check          | Action                                      |
    | -------------- | ------------------------------------------- |
    | Out of gas?    | Compare submitted vs recommended `gasLimit` |
    | Allowance?     | Check `allowance(owner, spender)`           |
    | Balance?       | Check `balanceOf` at execution block        |
    | Missing value? | Compare transaction value vs required value |
    | Slippage?      | Compare `minOut` vs actual output           |
    | Oracle?        | Look for stale price or wrong feed ID       |
    | Token issue?   | Check for transfer reverts or false returns |
  </Step>

  <Step title="Simulate the Transaction">
    Use Tenderly or Blocksec to reproduce the failure with identical parameters.
  </Step>

  <Step title="Test Single Changes">
    Modify one variable at a time (gas, value, approval, slippage) until the simulation succeeds.
  </Step>
</Steps>

***

## Quick Reference

| Failure           | Key Indicator                       | Fix                                               |
| ----------------- | ----------------------------------- | ------------------------------------------------- |
| Out of gas        | Trace ends abruptly, OOG error      | Use `gasLimit` from quote                         |
| Allowance         | `transfer amount exceeds allowance` | Approve correct spender                           |
| Balance           | `insufficient balance`              | Re-quote and verify balance                       |
| Missing value     | Native transfer fails               | Include `msg.value` from API                      |
| Slippage          | Min output check fails              | Re-quote first, then cautiously increase slippage |
| Stale oracle      | `StalePrice` errors                 | Report to LI.FI support                           |
| Token restriction | `SafeERC20: low-level call failed`  | Report token for deny list                        |
| Broken pool       | Math convergence fails              | Report pool for blacklist                         |
| Reentrancy        | `LOCKED` errors                     | Report pool for blacklist                         |
| Deadline expired  | `EXPIRED`                           | Re-quote and execute quickly                      |

***

## Related Resources

<CardGroup cols={2}>
  <Card title="Error Codes" icon="circle-exclamation" href="/api-reference/error-codes">
    API error code reference
  </Card>

  <Card title="Common Issues FAQ" icon="circle-question" href="/faqs/troubleshooting">
    Frequently asked troubleshooting questions
  </Card>

  <Card title="Status Tracking" icon="clock" href="/introduction/user-flows-and-examples/status-tracking">
    Track transaction status
  </Card>

  <Card title="Slippage & Price Impact" icon="chart-mixed" href="/faqs/slippage-price-impact">
    Understand slippage settings
  </Card>
</CardGroup>
