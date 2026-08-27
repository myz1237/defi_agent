"""Unit tests for Reciprocal Rank Fusion (pure, no DB)."""

from app.agent.knowledge.store import _rrf


def test_rrf_boosts_items_ranked_by_both():
    dense = [1, 2, 3]
    bm25 = [3, 4, 1]
    out = _rrf(dense, bm25, k=4)
    # 1 (dense#1, bm25#3) and 3 (dense#3, bm25#1) appear in both lists -> they outrank the single-list items
    assert set(out[:2]) == {1, 3}


def test_rrf_dedups_and_respects_k():
    out = _rrf([1, 2, 3, 4, 5], [5, 4], k=3)
    assert len(out) == 3 and len(set(out)) == 3


def test_rrf_single_list_preserves_rank_order():
    assert _rrf([10, 20, 30], k=2) == [10, 20]


def test_rrf_empty_lists():
    assert _rrf([], [], k=5) == []
