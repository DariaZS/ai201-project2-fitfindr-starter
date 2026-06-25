# agent.py

import re

from tools import create_fit_card, search_listings, suggest_outfit


def _new_session(query: str, wardrobe: dict) -> dict:
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


def _parse_query(query: str) -> dict:
    """
    Extract description, size, and max_price from natural language query.
    Uses regex — no LLM call needed for this step.
    """
    # Extract max price: "under $30", "$30", "30 dollars"
    price_match = re.search(r'\$(\d+(?:\.\d+)?)|under\s+\$?(\d+(?:\.\d+)?)', query, re.IGNORECASE)
    max_price = None
    if price_match:
        max_price = float(price_match.group(1) or price_match.group(2))

    # Extract size: "size M", "in M", "size XL", "W30", "S/M"
    size_match = re.search(
        r'\bsize\s+([A-Z0-9/]+)\b|\bin\s+(XS|S|M|L|XL|XXL|XXS)\b|\b(W\d{2}\s*L?\d*)\b|\b(XS|S/M|M|L|XL|XXL)\b',
        query, re.IGNORECASE
    )
    size = None
    if size_match:
        size = next(g for g in size_match.groups() if g is not None).strip()

    # Description: remove price and size mentions, clean up
    description = re.sub(r'(under\s+)?\$\d+(?:\.\d+)?', '', query, flags=re.IGNORECASE)
    description = re.sub(r'\bsize\s+[A-Z0-9/]+\b', '', description, flags=re.IGNORECASE)
    description = re.sub(r'\b(in\s+)?(XS|S/M|M|L|XL|XXL|XXS)\b', '', description, flags=re.IGNORECASE)
    description = re.sub(r'\b(looking for|i want|find me|i need)\b', '', description, flags=re.IGNORECASE)
    description = ' '.join(description.split())  # collapse whitespace

    return {
        "description": description,
        "size": size,
        "max_price": max_price,
    }


def run_agent(query: str, wardrobe: dict) -> dict:
    # Step 1: Initialize session
    session = _new_session(query, wardrobe)

    # Step 2: Parse query
    session["parsed"] = _parse_query(query)
    parsed = session["parsed"]

    # Step 3: Search listings
    session["search_results"] = search_listings(
        description=parsed["description"],
        size=parsed["size"],
        max_price=parsed["max_price"],
    )

    if not session["search_results"]:
        session["error"] = (
            f"No listings matched your search. "
            f"Try a broader description, different size, or higher budget. "
            f"(Searched for: '{parsed['description']}'"
            + (f", size {parsed['size']}" if parsed["size"] else "")
            + (f", under ${parsed['max_price']:.0f}" if parsed["max_price"] else "")
            + ")"
        )
        return session

    # Step 4: Select top result
    session["selected_item"] = session["search_results"][0]

    # Step 5: Suggest outfit
    session["outfit_suggestion"] = suggest_outfit(
        new_item=session["selected_item"],
        wardrobe=session["wardrobe"],
    )

    # Step 6: Create fit card
    session["fit_card"] = create_fit_card(
        outfit=session["outfit_suggestion"],
        new_item=session["selected_item"],
    )

    # Step 7: Return session
    return session


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"Selected item id: {session['selected_item']['id']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
    print(f"fit_card is None: {session2['fit_card'] is None}")