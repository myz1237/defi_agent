> ## Documentation Index
> Fetch the complete documentation index at: https://docs.li.fi/llms.txt
> Use this file to discover all available pages before exploring further.

# Fetching a Quote/Route

> Guide to make a quote and route request

## Using SDK

```TypeScript theme={"system"}
import { getRoutes } from '@lifi/sdk';

const routesRequest: RoutesRequest = {
  fromChainId: 42161, // Arbitrum
  toChainId: 10, // Optimism
  fromTokenAddress: '0xaf88d065e77c8cC2239327C5EDb3A432268e5831', // USDC on Arbitrum
  toTokenAddress: '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1', // DAI on Optimism
  fromAmount: '10000000', // 10 USDC
};

const result = await getRoutes(routesRequest);
const routes = result.routes;
```

When you make a route request, you receive an array of route objects containing the essential information to determine which route to take for a swap or bridging transfer. At this stage, transaction data is not included and must be requested separately.

Additionally, if you would like to receive just one best option that our smart routing API can offer, it might be better to request a quote using getQuote.

## Using API

To generate a quote based on the amount you are sending, use the /quote endpoint. This method is useful when you know the exact amount you want to send and need to calculate how much the recipient will receive.

```TypeScript theme={"system"}
const getQuote = async (fromChain, toChain, fromToken, toToken, fromAmount, fromAddress) => {
    const result = await axios.get('https://li.quest/v1/quote', {
        params: {
            fromChain,
            toChain,
            fromToken,
            toToken,
            fromAmount,
            fromAddress,
        }
    });
    return result.data;
}

const fromChain = 42161;
const fromToken = 'USDC';
const toChain = 10;
const toToken = 'USDC';
const fromAmount = '1000000';
const fromAddress = YOUR_WALLET_ADDRESS;

const quote = await getQuote(fromChain, toChain, fromToken, toToken, fromAmount, fromAddress);
```
