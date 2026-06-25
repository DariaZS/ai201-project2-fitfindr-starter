# FitFindr 🛍️

A multi-tool AI agent that helps users find secondhand clothing and figure out how to wear it. FitFindr searches mock thrift listings, suggests outfit combinations using the user's existing wardrobe, and generates a shareable fit card caption — all from a single natural language query.

Built for CodePath AI201 Project 2.

## What's Included
```
ai201-project2-fitfindr-starter/

├── data/

│   ├── listings.json          # 40 mock secondhand listings

│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe

├── utils/

│   └── data_loader.py         # Helper functions for loading the data

├── tools.py                   # Three core tools: search, suggest, fit card

├── agent.py                   # Planning loop and session state

├── app.py                     # Gradio UI

├── tests/

│   └── test_tools.py          # pytest tests for all three tools

├── planning.md                # Agent design spec

└── requirements.txt           # Python dependencies
```
## Setup

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```
Run the app:
```bash
python app.py
```

## Tool Inventory

### `search_listings(description, size, max_price)`
- **description** (str): Natural language keywords describing the item (e.g. "vintage graphic tee")
- **size** (str | None): Size filter, case-insensitive substring match. Pass None to skip.
- **max_price** (float | None): Maximum price inclusive. Pass None to skip.
- **Returns:** List of matching listing dicts sorted by relevance score (keyword overlap against title, description, style_tags, colors, brand). Empty list if nothing matches — no exception raised.

### `suggest_outfit(new_item, wardrobe)`
- **new_item** (dict): A listing dict returned by search_listings
- **wardrobe** (dict): Wardrobe dict with an `items` key containing a list of wardrobe item dicts. May be empty.
- **Returns:** Non-empty string with 1–2 outfit suggestions referencing specific wardrobe pieces by name. If wardrobe is empty, returns general styling advice based on the item's style tags.

### `create_fit_card(outfit, new_item)`
- **outfit** (str): Outfit suggestion string from suggest_outfit
- **new_item** (dict): The listing dict for the thrifted item
- **Returns:** 2–4 sentence casual Instagram/TikTok-style caption mentioning item name, price, and platform. If outfit is empty, returns a fallback caption built from item fields. Never raises an exception.

---

## Interaction Walkthrough

**User query:** "vintage graphic tee under $30"

**Step 1 — Tool called:**
- Tool: `search_listings`
- Input: `description="vintage graphic tee"`, `size=None`, `max_price=30.0`
- Why this tool: The user's query is parsed first to extract keywords and constraints. search_listings runs before any LLM call — it filters the dataset and scores results by keyword overlap. If it returns empty, the agent stops here.
- Output: `[{"id": "lst_002", "title": "Y2K Baby Tee — Butterfly Print", "price": 18.0, "platform": "depop", "size": "S/M", "condition": "excellent", ...}]` — top result selected as `session["selected_item"]`

**Step 2 — Tool called:**
- Tool: `suggest_outfit`
- Input: `new_item=session["selected_item"]` (Y2K Baby Tee dict), `wardrobe=get_example_wardrobe()` (10 wardrobe items)
- Why this tool: search_listings returned a result, so the agent proceeds. suggest_outfit receives the exact dict stored in session — no re-parsing of the original query.
- Output: "First, pair the Y2K Baby Tee with your Baggy straight-leg jeans and Chunky white sneakers. The fitted crop length creates a cute contrast with the loose, high-waisted jeans. Top it off with your Vintage black denim jacket for a chic, laid-back vibe. For a second look, try the tee with your Wide-leg khaki trousers and Black combat boots..."

**Step 3 — Tool called:**
- Tool: `create_fit_card`
- Input: `outfit=session["outfit_suggestion"]`, `new_item=session["selected_item"]`
- Why this tool: suggest_outfit returned a non-empty string, so the agent proceeds to generate the shareable caption. Both inputs come directly from session — no user re-entry.
- Output: "I just scored the cutest Y2K Baby Tee with a butterfly print on Depop for $18.00 and I'm obsessed! I paired it with my baggy jeans and chunky white sneakers for a fresh, casual look that's perfect for everyday wear. 🦋💛"

**Final output to user:**
Three panels in the Gradio UI — listing details (title, price, platform, size, condition, description), outfit suggestion, and fit card caption ready to copy.

---

## Error Handling and Fail Points

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | No listings match the query | Sets `session["error"]`: "No listings matched your search. Try a broader description, different size, or higher budget. (Searched for: 'designer ballgown', size XXS, under $5)" — agent returns immediately, `suggest_outfit` and `create_fit_card` are never called, `fit_card` remains None |
| `suggest_outfit` | Wardrobe is empty (`wardrobe["items"] == []`) | Prompt switches to general styling advice: LLM suggests what types of pieces pair well based on the item's style_tags and colors, without referencing specific wardrobe items. Still returns a non-empty string and proceeds to create_fit_card. |
| `create_fit_card` | `outfit` is empty or whitespace-only | Returns fallback caption using item fields directly: `"just thrifted this y2k baby tee — butterfly print from depop for $18.00 🛍️"` — no exception raised, no crash |

---

## AI Usage

### Instance 1 — Tool implementations (Milestone 3)
**Input to Claude:** The Tool 1–3 spec blocks from `planning.md` (inputs, return values, failure modes for each tool) plus the `tools.py` stub file with docstrings.  
**Output:** Complete implementations of all three functions.  
**What I changed:** The original `search_listings` scoring only matched against `title` and `style_tags`. I expanded it to also search `description`, `colors`, and `brand` so that queries like "red flannel" surface the Woolrich listing. I verified the price and size filter logic manually against 3 test cases before accepting the output.

### Instance 2 — Planning loop (Milestone 4)
**Input to Claude:** The Planning Loop and State Management sections of `planning.md` plus the ASCII architecture diagram and the `agent.py` stub file.  
**Output:** Complete `run_agent()` with `_parse_query()` using regex for description, size, and price extraction.  
**What I changed:** The original regex missed numeric shoe sizes like "size 8". I updated the size pattern to capture numeric values. I also ran the no-results branch explicitly with the ballgown query to confirm `fit_card` was None before accepting the implementation.

---

## Spec Reflection

**One way planning.md helped during implementation:**
The ASCII architecture diagram in planning.md made the conditional branching concrete before I wrote a single line of agent code. When I gave Claude the diagram alongside the planning loop spec, the generated `run_agent()` correctly placed the early-return after `search_listings` on the first attempt — the diagram communicated the structure more precisely than the text description alone would have.

**One divergence from your spec, and why:**
The spec described the query parser as a potential LLM call. I implemented it as regex instead. The LLM approach would handle edge cases like "I'm a medium" or "fits between a 6 and 8" better, but regex costs zero latency and no API tokens per query. Since the mock dataset uses standard size strings, regex covers all real test cases. A production version with freeform user input would warrant the LLM parser.

## Demo
```
https://youtu.be/wMBZGlOLkRc
```