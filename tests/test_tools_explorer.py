"""Explorer tools with a fake web3 (monkeypatched) and respx-mocked 4byte."""

import httpx
import respx
from hexbytes import HexBytes
from web3 import Web3

import app.agent.tools.explorer as ex


class _Eth:
    def __init__(self, tx=None, receipt=None, balance=None):
        self._tx, self._receipt, self._balance = tx, receipt, balance

    def get_transaction(self, _h):
        return self._tx

    def get_transaction_receipt(self, _h):
        return self._receipt

    def get_balance(self, _a):
        return self._balance


class _W3:
    def __init__(self, eth):
        self.eth = eth


def test_unsupported_chain_no_network():
    out = ex.get_transaction.invoke({"tx_hash": "0x1", "chain": "solana"})
    assert "Unsupported chain" in out


def test_get_transaction(monkeypatch):
    tx = {
        "input": HexBytes("0x0193b9fc"),
        "blockNumber": 123,
        "from": "0xAAA",
        "to": "0xBBB",
        "value": 10**18,
        "nonce": 5,
        "gas": 21000,
        "gasPrice": 1000,
    }
    monkeypatch.setattr(ex, "get_web3", lambda _k: _W3(_Eth(tx=tx)))
    out = ex.get_transaction.invoke({"tx_hash": "0x1"})
    assert "block=123" in out
    assert "to=0xBBB" in out
    assert "selector=0x0193b9fc" in out
    assert "value=1 " in out  # 1e18 wei -> 1 ether


def test_receipt_erc20_decode(monkeypatch):
    addr1, addr2 = "1" * 40, "2" * 40
    log = {
        "address": "0xToken",
        "topics": [
            HexBytes(Web3.keccak(text="Transfer(address,address,uint256)")),
            HexBytes("0x" + "00" * 12 + addr1),
            HexBytes("0x" + "00" * 12 + addr2),
        ],
        "data": HexBytes((1000).to_bytes(32, "big")),
    }
    receipt = {"status": 1, "gasUsed": 50000, "logs": [log]}
    monkeypatch.setattr(ex, "get_web3", lambda _k: _W3(_Eth(receipt=receipt)))
    out = ex.get_transaction_receipt_logs.invoke({"tx_hash": "0x1"})
    assert "status=success" in out
    assert "ERC20 Transfer" in out
    assert "amount(raw)=1000" in out
    assert Web3.to_checksum_address("0x" + addr1) in out


def test_get_balances(monkeypatch):
    monkeypatch.setattr(ex, "get_web3", lambda _k: _W3(_Eth(balance=10**18)))
    out = ex.get_balances.invoke({"address": "0x" + "a" * 40})
    assert "native balance" in out
    assert "= 1" in out


def test_resolve_ens(monkeypatch):
    class _Ens:
        def address(self, _n):
            return "0xRESOLVED"

    class _W3Ens:
        ens = _Ens()

    monkeypatch.setattr(ex, "get_ens_web3", lambda: _W3Ens())
    out = ex.resolve_ens.invoke({"name": "vitalik.eth"})
    assert "0xRESOLVED" in out


def test_resolve_ens_rejects_non_ens():
    assert "not an ENS name" in ex.resolve_ens.invoke({"name": "0xabc"})


@respx.mock
def test_decode_transaction_4byte(monkeypatch):
    tx = {"input": HexBytes("0x0193b9fc" + "00" * 32)}
    monkeypatch.setattr(ex, "get_web3", lambda _k: _W3(_Eth(tx=tx)))
    respx.get("https://www.4byte.directory/api/v1/signatures/").mock(
        return_value=httpx.Response(
            200, json={"results": [{"id": 1, "text_signature": "callDiamondWithPermit2(bytes)"}]}
        )
    )
    out = ex.decode_transaction.invoke({"tx_hash": "0x1"})
    assert "selector=0x0193b9fc" in out
    assert "callDiamondWithPermit2(bytes)" in out
