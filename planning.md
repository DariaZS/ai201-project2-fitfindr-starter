# FitFindr — planning.md

---

## Tools

### Tool 1: search_listings

**What it does:**
Searches the mock listings dataset for items matching the user's description, size, and budget. Returns a ranked list of matching listings or an empty list if nothing matches.

**Input parameters:**
- `description` (str): Natural language description of the item (e.g. "vintage graphic tee")
- `size` (str): Size filter (e.g. "M", "W30 L30", "XL")
- `max_price` (float): Maximum price the user is willing to pay

**What it returns:**
A list of matching listing dicts, each containing: id, title, description, category, style_tags, size, condition, price, colors, brand, platform. Sorted by relevance (style_tags match count).

**What happens if it fails or returns nothing:**
Agent notifies the user that no listings matched and suggests adjusting size, price, or description. Does NOT proceed to suggest_outfit. Optionally retries with loosened constraints (stretch: remove size filter).

---

### Tool 2: suggest_outfit

**What it does:**
Given a newly found listing and the user's wardrobe, uses the LLM to suggest one or more complete outfit combinations using existing wardrobe pieces.

**Input parameters:**
- `new_item` (dict): A single listing dict returned by search_listings
- `wardrobe` (dict): Wardrobe dict with an `items` key (from get_example_wardrobe() or user input)

**What it returns:**
A string describing one or more outfit combinations, referencing specific wardrobe pieces by name.

**What happens if it fails or returns nothing:**
If wardrobe is empty, agent informs user and generates a generic styling suggestion based on the item's style_tags alone. If LLM call fails, agent returns a fallback message and skips create_fit_card.

---

### Tool 3: create_fit_card

**What it does:**
Generates a short, casual, shareable caption for the outfit — written in the voice of someone posting to Instagram or TikTok.

**Input parameters:**
- `outfit` (str): The outfit suggestion string returned by suggest_outfit
- `new_item` (dict): The listing dict so the caption can reference price, platform, item name

**What it returns:**
A single string: a 1-3 sentence caption with casual tone, relevant emoji, and specific details (price, platform, key pieces).

**What happens if it fails or returns nothing:**
If outfit string is empty or LLM fails, agent returns a minimal fallback caption using just the new_item fields (title + price + platform).

---

### Additional Tools (if any)

### Tool 4: compare_price (stretch)

**What it does:**
Given a listing, compares its price to similar items in the dataset to estimate whether it's a good deal.

**Input parameters:**
- `item` (dict): A listing dict

**What it returns:**
A string: "good deal", "fair price", or "overpriced", plus the average price of comparable items.

**What happens if it fails or returns nothing:**
If no comparable items found, returns "not enough data to compare" and proceeds without blocking the main flow.

---

## Planning Loop

The agent runs a sequential loop with conditional branching:

1. Parse user input → extract description, size, max_price, and any wardrobe info
2. Call search_listings → if empty: report to user and STOP
3. Pick top result from listings → call suggest_outfit with top result + wardrobe
4. If suggest_outfit returns empty: report fallback message and STOP before fit card
5. Call create_fit_card with outfit + new_item
6. Return final fit card to user

The loop does not call tools in a fixed sequence — step 3 only runs if step 2 returned results, and step 5 only runs if step 3 succeeded. The agent checks return values at each step before proceeding.

---

## State Management

A session state dict is maintained across tool calls:

```python
state = {
    "user_query": str,         # original user message
    "search_results": list,    # returned by search_listings
    "selected_item": dict,     # top result chosen from search_results
    "wardrobe": dict,          # user wardrobe (example or user-provided)
    "outfit_suggestion": str,  # returned by suggest_outfit
    "fit_card": str            # returned by create_fit_card
}
```

Each tool reads from and writes to this state dict. No tool receives raw user input directly after step 1 — everything flows through state.

---

## Error Handling

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | "No listings matched your search. Try a broader description, different size, or higher budget." Stop — do not call suggest_outfit. |
| suggest_outfit | Wardrobe is empty | G"Your wardrobe is empty — here are some general styling tips for this piece based on its style." Proceed to fit card with generic suggestion. |
| create_fit_card | Outfit input is missing or incomplete | "Here's a simple caption for this find: '[title] from [platform] for $[price] 🛍️'" Use new_item fields as fallback. |

---

## Architecture