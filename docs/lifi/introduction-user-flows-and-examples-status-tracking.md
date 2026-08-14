> ## Documentation Index
> Fetch the complete documentation index at: https://docs.li.fi/llms.txt
> Use this file to discover all available pages before exploring further.

# Transaction Status Tracking

> Complete guide to checking cross-chain transaction statuses using the LI.FI API

# Transaction Status

This guide explains how to check the status of cross-chain and swap transactions using the `/status` endpoint provided by LI.FI.

***

## Querying the Status Endpoint

To fetch the status of a transfer, the `/status` endpoint can be queried with:

1. sending transaction hash
2. receiving transaction hash
3. transactionId

<Note>
  Only one of the above values are required and need to be passed in `txHash` param.
</Note>

### Required:

* `txHash`

### Optional:

* `fromChain`: Speeds up the request (recommended)
* `toChain`
* `bridge`

For swap transactions, set `fromChain` and `toChain` to the same value. The `bridge` parameter can be omitted.

```typescript theme={"system"}
const getStatus = async (txHash: string) => {
  const result = await axios.get('https://li.quest/v1/status', {
    params: { txHash },
  });
  return result.data;
};
```

## Sample Response

```json theme={"system"}
{
  "transactionId": "0x0959ee0fbb37a868752d7ae40b25dbfa3b7d72f499fa8386fd5f4105b18b62bd",
  "sending": {
    "txHash": "0x5862726dbc6643c6a34b3496bb15e91f11771f6756ccf83826304846bbc93c0v",
    "txLink": "https://etherscan.io/tx/0x5862726dbc6643c6a34b3496bb15e91f11771f6756ccf83826304846bbc93c0v",
    "amount": "60000000000000000000000",
    "token": {
      "symbol": "ORDS",
      "priceUSD": "0.012027801612559667"
    },
    "gasPrice": "23079962248",
    "gasUsed": "231727",
    "gasAmountUSD": "14.0296",
    "amountUSD": "721.6681",
    "includedSteps": [
      {
        "tool": "feeCollection",
        "fromAmount": "60000000000000000000000",
        "toAmount": "59820000000000000000000"
      },
      {
        "tool": "1inch",
        "fromAmount": "59820000000000000000000",
        "toAmount": "275101169247651913"
      }
    ]
  },
  "receiving": {
    "txHash": "0x2862726dbc6643c6a34b3496bb15e91f11771f6756ccf83826604846bbc93c0v",
    "amount": "275101169247651913",
    "token": {
      "symbol": "ETH",
      "priceUSD": "2623.22"
    },
    "gasAmountUSD": "14.0296",
    "amountUSD": "721.6509"
  },
  "lifiExplorerLink": "https://scan.li.fi/tx/0x5862726dbc6643c6a34b3496bb15e91f11771f6756ccf83826304846bbc93c0e",
  "fromAddress": "0x14a980237fa9797fa27c5152c496cab65e36da4f",
  "toAddress": "0x14a980237fa9797fa27c5152c496cab65e36da4f",
  "tool": "1inch",
  "status": "DONE",
  "substatus": "COMPLETED",
  "substatusMessage": "The transfer is complete.",
  "metadata": {
    "integrator": "example_integrator"
  }
}
```

***

## Status Values

| Status      | Description                                 |
| ----------- | ------------------------------------------- |
| `NOT_FOUND` | Transaction doesn't exist or not yet mined. |
| `INVALID`   | Hash is not tied to the requested tool.     |
| `PENDING`   | Bridging is still in progress.              |
| `DONE`      | Transaction completed successfully.         |
| `FAILED`    | Bridging process failed.                    |

***

## Substatus Definitions

### PENDING

* `WAIT_SOURCE_CONFIRMATIONS`: Waiting for source chain confirmations
* `WAIT_DESTINATION_TRANSACTION`: Waiting for destination transaction
* `BRIDGE_NOT_AVAILABLE`: Bridge API is unavailable
* `CHAIN_NOT_AVAILABLE`: Source/destination chain RPC unavailable
* `REFUND_IN_PROGRESS`: Refund in progress (if supported)
* `UNKNOWN_ERROR`: Status is indeterminate

### DONE

* `COMPLETED`: Transfer was successful
* `PARTIAL`: Only partial transfer completed (common for across, hop, stargate, amarok)
* `REFUNDED`: Tokens were refunded

### FAILED

* `NOT_PROCESSABLE_REFUND_NEEDED`: Cannot complete, refund needed
* `OUT_OF_GAS`: Transaction ran out of gas
* `SLIPPAGE_EXCEEDED`: Received amount too low
* `INSUFFICIENT_ALLOWANCE`: Not enough allowance
* `INSUFFICIENT_BALANCE`: Not enough balance
* `EXPIRED`: Transaction expired
* `UNKNOWN_ERROR`: Unknown or invalid state
* `REFUNDED`: Tokens were refunded
