> ## Documentation Index
> Fetch the complete documentation index at: https://docs.li.fi/llms.txt
> Use this file to discover all available pages before exploring further.

# Universal Market Access for Digital Assets

> One Integration. Every Chain. Every Asset. Every Liquidity Source.

LI.FI is the routing and execution layer that connects any application to all on-chain liquidity across chains, bridges, DEXs, solvers, and yield protocols through a single integration.

## Why LI.FI

Blockchain infrastructure is fragmented across:

* Dozens of chains and rollups
* Multiple bridge protocols
* DEX aggregators per ecosystem
* Different token standards (USDC, USDC.e, wrapped assets, native gas tokens)
* Emerging intent and solver networks
* RWAs and hundreds of stablecoins
* Yield opportunities and money markets
* Perps DEXs & Orderbooks

Integrating these systems individually is expensive, brittle, and difficult to maintain. Data management and customer support tooling is painful on top.

**LI.FI abstracts this complexity behind a single integration.**

***

## What LI.FI Provides

LI.FI is the routing and orchestration layer that enables:

* Same-chain swaps
* Cross-chain swaps & bridging
* Cross-chain contract calls
* Multi-step transaction flows (bridge → swap → zap → deposit)
* Finding and buying perps
* Finding and zapping into yield opportunities

All through one unified API and SDK.

***

## How It Works

LI.FI sits between your application and the fragmented liquidity landscape.

<Steps>
  <Step title="Aggregates">
    Bridges, DEXs, Solvers, Perp Orderbooks, and Yield protocols into a single interface.
  </Step>

  <Step title="Normalizes">
    Token standards and chain differences so your app never has to handle them directly.
  </Step>

  <Step title="Calculates">
    Optimal routes based on price, speed, gas cost, and execution reliability.
  </Step>

  <Step title="Executes">
    Transactions with built-in monitoring and fallback logic to maximise success.
  </Step>
</Steps>

You integrate once. LI.FI handles the routing logic and infrastructure maintenance.

***

## Core Capabilities

<CardGroup cols={2}>
  <Card title="Unified Routing" icon="route">
    Access liquidity across major chains and ecosystems without maintaining individual integrations.
  </Card>

  <Card title="Smart Order Routing" icon="brain">
    Routes are optimised for best price, gas efficiency, execution success rate, and speed.
  </Card>

  <Card title="Execution Monitoring & Fallbacks" icon="shield-check">
    If a provider fails or a route becomes invalid, LI.FI automatically re-routes to maximise transaction success.
  </Card>

  <Card title="Token Standard Abstraction" icon="layer-group">
    Canonical token mapping prevents failures from wrapped assets and bridged variants (e.g. USDC vs USDC.e).
  </Card>

  <Card title="Cross-Chain Composability" icon="link">
    Build programmable multi-step flows: swap + bridge, bridge + deposit, cross-chain zaps, and full DeFi workflows.
  </Card>
</CardGroup>

***

## When to Use LI.FI

LI.FI is built for any application that requires reliable on-chain execution:

* Wallets & Wallet-as-a-Service
* Exchanges & trading desks
* Fintechs, neobanks & Banking-as-a-Service
* DeFi applications
* On-ramp / off-ramp providers
* AI agents executing on-chain

If your users need to move assets across chains or interact with fragmented liquidity, LI.FI removes the infrastructure burden.

***

## Without LI.FI vs. With LI.FI

|                         | Without LI.FI                       | With LI.FI                      |
| ----------------------- | ----------------------------------- | ------------------------------- |
| **Bridges**             | Integrate one per chain pair        | Covered by a single integration |
| **DEX aggregators**     | Integrate one per ecosystem         | Included out of the box         |
| **Token mapping**       | Build and maintain manually         | Handled automatically           |
| **Failed transactions** | Monitor and recover yourself        | Built-in fallback routing       |
| **New chain support**   | Re-integrate each time              | Continuous expansion by LI.FI   |
| **Data feeds**          | Aggregate and map dozens of sources | Unified data layer              |
| **Maintenance**         | Ongoing, high overhead              | Managed by LI.FI                |
| **Time to market**      | Weeks to months per integration     | Days                            |

***

## Next Steps

<CardGroup cols={3}>
  <Card title="SDK Integration" icon="code" href="/sdk/overview" onClick={() => window.plausible?.('next_steps_sdk_integration_click')}>
    Integrate LI.FI into your application using the JavaScript/TypeScript SDK for full control over routes, execution, and token management.
  </Card>

  <Card title="API Reference" icon="webhook" href="/api-reference/introduction" onClick={() => window.plausible?.('next_steps_api_reference_click')}>
    Explore the LI.FI REST API to fetch quotes, execute cross-chain transfers, and track transaction status directly via HTTP.
  </Card>

  <Card title="Widget" icon="window" href="/widget/overview" onClick={() => window.plausible?.('next_steps_widget_click')}>
    Drop in the ready-made swap and bridge widget for an instant, customizable cross-chain UI in your app.
  </Card>
</CardGroup>
