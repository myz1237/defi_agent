> ## Documentation Index
> Fetch the complete documentation index at: https://docs.li.fi/llms.txt
> Use this file to discover all available pages before exploring further.

# Quote vs Route

> Difference between /quote and /advanced/routes

## /quote

/quote endpoint returns **the best single-step route only**. So only one route is returned and it includes transaction data that is needed to be sent onchain to execute the route.

## /advanced/routes

The `/advanced/routes` endpoint allows more complex routes, in which the user needs to bridge funds first and then needs to trigger a second transaction on the destination chain to swap into the desired asset.

After retrieving the routes, the tx data needs to be generated and retrieved using the `/advanced/stepTransaction` endpoint. This endpoint expects a full Step object which usually is retrieved by calling the `/advanced/routes` endpoint and selecting the most suitable Route.

The `/advanced/stepTransaction` endpoint needs to be called to retrieve transaction data for every Step. Internally both endpoints use the same routing algorithm, but with the described different settings.

<Note>
  The `/advanced/routes` endpoint can return single-step routes only by using the `allowChainSwitch: false` parameter in the request.
</Note>
