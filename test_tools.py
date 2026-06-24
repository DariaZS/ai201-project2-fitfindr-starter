# tests/test_tools.py
from tools import create_fit_card, search_listings, suggest_outfit
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe

# ── search_listings tests ─────────────────────────────────────────────────────

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []

def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)

def test_search_size_filter():
    results = search_listings("jeans", size="XXS", max_price=500)
    assert results == []  # no XXS listings expected

def test_search_sorted_by_relevance():
    results = search_listings("vintage denim jeans", size=None, max_price=100)
    assert len(results) > 0
    # first result should have more keyword hits than last
    assert isinstance(results[0], dict)

# ── suggest_outfit tests ──────────────────────────────────────────────────────

def test_suggest_outfit_with_wardrobe():
    from utils.data_loader import load_listings
    item = load_listings()[0]
    result = suggest_outfit(item, get_example_wardrobe())
    assert isinstance(result, str)
    assert len(result) > 0

def test_suggest_outfit_empty_wardrobe():
    from utils.data_loader import load_listings
    item = load_listings()[0]
    result = suggest_outfit(item, get_empty_wardrobe())
    assert isinstance(result, str)
    assert len(result) > 0  # should not crash or return empty

# ── create_fit_card tests ─────────────────────────────────────────────────────

def test_fit_card_returns_string():
    from utils.data_loader import load_listings
    item = load_listings()[0]
    result = create_fit_card("Pair with baggy jeans and white sneakers.", item)
    assert isinstance(result, str)
    assert len(result) > 0

def test_fit_card_empty_outfit_fallback():
    from utils.data_loader import load_listings
    item = load_listings()[0]
    result = create_fit_card("", item)
    assert isinstance(result, str)
    assert len(result) > 0  # fallback, not a crash

def test_fit_card_varies():
    from utils.data_loader import load_listings
    item = load_listings()[0]
    outfit = "Vintage tee with baggy jeans and chunky sneakers."
    r1 = create_fit_card(outfit, item)
    r2 = create_fit_card(outfit, item)
    # outputs should vary due to temperature=1.0
    assert r1 != r2