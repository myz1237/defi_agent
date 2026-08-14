> ## Documentation Index
> Fetch the complete documentation index at: https://docs.li.fi/llms.txt
> Use this file to discover all available pages before exploring further.

# Route availability

<Accordion title="What does the error message 'Return amount is not enough' mean?">
  This slippage error appears when the expected return amount is lower than the minimum accepted threshold.
  It often happens due to market volatility or low liquidity.
</Accordion>

<Accordion title="What should I do if I encounter the error 'Exchange rate has changed'?">
  This error indicates a price change between the quote and execution.
  To resolve it, increase the slippage tolerance. Be cautious—higher slippage can result in worse rates.

  If you're using the SDK, implement <code>acceptExchangeRateUpdateHook</code> and return <code>true</code> to accept updated rates automatically.
  Refer to the SDK docs: [acceptExchangeRateUpdateHook](/sdk/execute-routes#acceptexchangerateupdatehook)
</Accordion>

<Accordion title="Why do I see the error 'EVM contract destination addresses not currently supported by mayanWH and mayanMCTP'?">
  Some versions of Mayan (mayanWH and mayanMCTP) do not support smart contract addresses as destinations.
</Accordion>

<Accordion title="Why did my Mayan MCTP transfer take long and cost more?">
  Mayan MCTP uses CCTP, which has slower settlement times and higher gas costs on Ethereum.
  It is generally used for large transfers when other bridges lack liquidity.
</Accordion>

<Accordion title="What does error code 1001: 'None of the available routes could successfully generate a tx' mean?">
  This usually means the <code>fromAddress</code> does not have enough funds to cover the transaction.
</Accordion>

<Accordion title="Why do I see the error 'Not an EVM Transaction' even though funds arrived?">
  This message appears when the transaction has not yet been indexed by LI.FI.
  Once it is indexed, the scanner will display its details.
</Accordion>

<Accordion title="What does error selector 0x963b34a5... mean in a failed swap?">
  This code likely represents a custom error from the DEX, such as <code>MinimalOutputBalanceViolation</code>.
  Most swap failures come from DEX-level checks. If not, LI.FI applies its own fallback checks.
  Error codes may vary by provider.
</Accordion>

<Accordion title="When is a failed transaction eligible for a refund, and can the status change afterward?">
  Refund policies depend on the bridge. Some bridges issue refunds automatically; others may leave transactions unresolved.
</Accordion>

<Accordion title="What does the NOT_PROCESSABLE_REFUND_NEEDED substatus mean?">
  This substatus usually comes from cBridge. It means the transfer could not be processed due to price, gas, or liquidity issues.
  LI.FI will then trigger a refund on the source chain.
</Accordion>

<Accordion title="What does the PARTIAL substatus mean in a transaction?">
  PARTIAL is a final status. The user receives the full value, but in a different token than expected.
</Accordion>

<Accordion title="Why don't I get quotes when bridging from a Solana wallet with no SOL?">
  LI.FI blocks quotes if the wallet has no SOL. This prevents failures from rent and gas fees.
  To fetch rates without requiring a funded wallet, use the <code>/advanced/routes</code> endpoint without specifying a wallet address.
</Accordion>

<Accordion title="What are intents and how do they fit into routing?">
  An intent states the desired outcome (e.g., "Swap 1 ETH on Ethereum into at least X USDC on Base"). LI.FI can pass intents to a solver marketplace where solvers compete to fulfill them. Routing may present intent-based execution alongside classic DEX aggregation and bridge routes; integrators see intents as another path under the same fee model.
</Accordion>
