> ## Documentation Index
> Fetch the complete documentation index at: https://docs.li.fi/llms.txt
> Use this file to discover all available pages before exploring further.

# Slippage and price impact

<Accordion title="Why is the toAmount lower than expected based on the slippage value?">
  <code>toAmount</code> is the estimated post-swap amount. <code>toAmountMin</code> is the minimum amount based on your slippage setting.

  A lower <code>toAmount</code> can result from price impact or market fluctuations.

  To filter out routes with high price impact, use the <code>maxPriceImpact</code> parameter.
</Accordion>

<Accordion title="What's the difference between slippage and price impact?">
  * <strong>Slippage</strong>: Difference between <code>toAmount</code> and <code>toAmountMin</code>
  * <strong>Price impact</strong>: Difference between the original quote and <code>toAmount</code>
</Accordion>

<Accordion title="How does slippage and toMinAmount works in routes with multistep transaction?">
  Our default slippage, when no slippage is set, is 0.5% per step (<code>0.005</code> on the API). Slippage is expressed as a decimal from <code>0</code> to <code>1</code>, where <code>1</code> = 100%.

  For example, a route that includes <code>swap + bridge + swap</code> can result in 1.5% total slippage in that sense, but there are some exceptions:

  * Some exchanges, such as those on Solana, may suggest their own slippage if none is set.
  * Some bridges, such as cBridge for small amounts, may enforce their own slippage to help ensure successful transaction execution. In those cases, we pass on that slippage.

  The API accepts manually set slippage of up to <code>1</code> or 100%, expressed as a decimal.

  We recommend not tracking the slippage set by the user directly, but instead tracking the <code>toAmountMin</code> from our quotes. This is the value we promise the user after slippage. If they receive less than this amount, something is likely off. We also track this on our side so we can investigate transactions that users report.
</Accordion>

<Accordion title="Does increasing slippage protect against exchange rate changes?">
  No. Increasing slippage tolerance does not prevent rate changes. It only widens the acceptable range before failing the transaction.
</Accordion>

<Accordion title="What slippage tolerance should I use for stablecoins or major tokens?">
  Use 0.5%. Slippage is typically minimal unless the trade size is very small or very large.
</Accordion>

<Accordion title="What is the best slippage value for cross-chain swaps?">
  It depends on the token, chain, and amount. There is no universal value.

  To reduce failures:

  * Execute the quote immediately
  * For Solana same-chain swaps, omit the slippage parameter to let LI.FI auto-calculate
</Accordion>

<Accordion title="How does LI.FI calculate price impact, and is there a minimum amount for filtering?">
  LI.FI calculates price impact using the difference in USD value between input and output tokens.

  Price impact filtering does not apply to trades under \$10.
</Accordion>

<Accordion title="How can I avoid slippage errors?">
  * Execute the quote immediately
  * Refresh the quote if delayed
  * Increase the allowed slippage in your API request
</Accordion>

<Accordion title="Do you guarantee what the user receives, and how does slippage work?">
  Yes. A minimum received amount is enforced when the user signs; execution must deliver at least that minimum or it reverts. Slippage exists because prices/liquidity move between quote and execution. Auto slippage picks a suitable buffer by asset liquidity (lower for stablecoins, higher for long-tail assets), and LI.FI commonly defaults to \~0.5% with the minimum slightly below the estimate to absorb normal movement.
</Accordion>
