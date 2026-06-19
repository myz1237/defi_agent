"""Explorer 工具:纯 RPC、按交易哈希/地址的只读查询(跨 5 链通用)。

不依赖第三方索引器。decode 用 4byte.directory 反查 selector;
日志解码内置 ERC20 Transfer(其余按原始 topic 返回)。
"""

import httpx
from langchain_core.tools import tool
from web3 import Web3

from app.agent.tools.base import ALL_CHAINS, make_spec
from app.agent.tools.registry import register
from app.chains.rpc import get_ens_web3, get_web3, resolve_chain_or_error
from app.config import settings

_TRANSFER_TOPIC = Web3.to_hex(Web3.keccak(text="Transfer(address,address,uint256)")).lower()


def _topic_to_address(topic_hex: str) -> str:
    return Web3.to_checksum_address("0x" + topic_hex[-40:])


def _lookup_4byte(selector: str) -> list[str]:
    try:
        r = httpx.get(
            "https://www.4byte.directory/api/v1/signatures/",
            params={"hex_signature": selector},
            timeout=settings.http_timeout,
        )
        results = r.json().get("results", [])
        # 4byte 可能有多条;按 id 升序(越早注册越可能是真实签名)
        results.sort(key=lambda x: x.get("id", 0))
        return [x["text_signature"] for x in results][:5]
    except Exception:
        return []


@tool
def get_transaction(tx_hash: str, chain: str = "ethereum") -> str:
    """按交易哈希获取交易基本信息(from/to/native value/gas/nonce/区块/selector)。

    chain: ethereum/bsc/arbitrum/base/optimism(默认 ethereum)。
    """
    chain_key, err = resolve_chain_or_error(chain)
    if err:
        return err
    try:
        tx = get_web3(chain_key).eth.get_transaction(tx_hash)
    except Exception as e:
        return f"查询交易失败({chain_key}):{e}"
    data = Web3.to_hex(tx["input"])
    selector = data[:10] if len(data) >= 10 else None
    return (
        f"链={chain_key} 区块={tx['blockNumber']}\n"
        f"from={tx['from']}\nto={tx['to']}\n"
        f"value={Web3.from_wei(tx['value'], 'ether')} (native) nonce={tx['nonce']}\n"
        f"gas={tx['gas']} gasPrice={tx['gasPrice']}\n"
        f"selector={selector} inputHexLen={len(data)}"
    )


@tool
def decode_transaction(tx_hash: str, chain: str = "ethereum") -> str:
    """解码交易 input 的函数选择器:经 4byte.directory 反查可能的函数签名。

    chain: ethereum/bsc/arbitrum/base/optimism。
    """
    chain_key, err = resolve_chain_or_error(chain)
    if err:
        return err
    try:
        tx = get_web3(chain_key).eth.get_transaction(tx_hash)
    except Exception as e:
        return f"查询交易失败({chain_key}):{e}"
    data = Web3.to_hex(tx["input"])
    if len(data) < 10:
        return "无 input data(可能是原生币转账 EOA→EOA,无函数调用)。"
    selector = data[:10]
    sigs = _lookup_4byte(selector)
    return (
        f"selector={selector}\n候选函数签名(4byte,可能多义):{sigs or '未找到'}\n"
        f"input 长度={len(data)} hex 字符(参数解码需合约 ABI)"
    )


@tool
def get_transaction_receipt_logs(tx_hash: str, chain: str = "ethereum") -> str:
    """获取交易收据与事件日志:状态/gasUsed,并解码 ERC20 Transfer(其余按原始 topic 返回)。

    chain: ethereum/bsc/arbitrum/base/optimism。
    """
    chain_key, err = resolve_chain_or_error(chain)
    if err:
        return err
    try:
        receipt = get_web3(chain_key).eth.get_transaction_receipt(tx_hash)
    except Exception as e:
        return f"查询收据失败({chain_key}):{e}"
    status = "success" if receipt["status"] == 1 else "failed"
    lines = [f"链={chain_key} status={status} gasUsed={receipt['gasUsed']} 日志数={len(receipt['logs'])}"]
    for i, lg in enumerate(receipt["logs"][:20]):
        topics = [Web3.to_hex(t) for t in lg["topics"]]
        if topics and topics[0].lower() == _TRANSFER_TOPIC and len(topics) == 3:
            amount = int(Web3.to_hex(lg["data"]), 16) if lg["data"] else 0
            lines.append(
                f"  [{i}] ERC20 Transfer token={lg['address']} "
                f"from={_topic_to_address(topics[1])} to={_topic_to_address(topics[2])} amount(raw)={amount}"
            )
        else:
            lines.append(f"  [{i}] {lg['address']} topic0={topics[0] if topics else None}")
    if len(receipt["logs"]) > 20:
        lines.append(f"  …(共 {len(receipt['logs'])} 条,仅显示前 20)")
    return "\n".join(lines)


@tool
def resolve_ens(name: str) -> str:
    """把 ENS 域名(如 vitalik.eth)解析为地址。走主网,返回的地址全链通用。"""
    if not name.lower().endswith(".eth"):
        return f"{name} 不是 ENS 域名(应以 .eth 结尾)。"
    try:
        addr = get_ens_web3().ens.address(name)
    except Exception as e:
        return f"ENS 解析失败:{e}"
    return f"{name} -> {addr}" if addr else f"{name} 未解析到地址(无 addr 记录)。"


@tool
def get_balances(address: str, chain: str = "ethereum") -> str:
    """查询地址的原生币余额。

    chain: ethereum/bsc/arbitrum/base/optimism。(ERC20 全量余额需索引器,暂不支持)
    """
    chain_key, err = resolve_chain_or_error(chain)
    if err:
        return err
    try:
        bal = get_web3(chain_key).eth.get_balance(Web3.to_checksum_address(address))
    except Exception as e:
        return f"查询余额失败({chain_key}):{e}"
    return f"{address} 在 {chain_key} 原生余额 = {Web3.from_wei(bal, 'ether')}"


# 注册(均为只读、跨所有受支持链)
register(make_spec(get_transaction, "explorer", ALL_CHAINS))
register(make_spec(decode_transaction, "explorer", ALL_CHAINS))
register(make_spec(get_transaction_receipt_logs, "explorer", ALL_CHAINS))
register(make_spec(resolve_ens, "explorer", ALL_CHAINS))
register(make_spec(get_balances, "explorer", ALL_CHAINS))
