from app.chains.registry import chain_id_to_key, get_chain, normalize_chain, supported_keys


def test_aliases_normalize():
    assert normalize_chain("eth") == "ethereum"
    assert normalize_chain("BNB") == "bsc"
    assert normalize_chain("arb") == "arbitrum"
    assert normalize_chain("op") == "optimism"
    assert normalize_chain(None) == "ethereum"


def test_supported_keys():
    assert set(supported_keys()) == {"ethereum", "bsc", "arbitrum", "base", "optimism"}


def test_get_chain():
    assert get_chain("solana") is None
    assert get_chain("ethereum").chain_id == 1
    assert get_chain("eth").chain_id == 1  # alias


def test_chain_id_to_key():
    assert chain_id_to_key(56) == "bsc"
    assert chain_id_to_key(8453) == "base"
    assert chain_id_to_key(99999) is None
