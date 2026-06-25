# Design Spec: Keyword Research Automation

This document outlines the design, component structure, data flow, and fallback strategies for the automated keyword research feature.

---

## 📋 1. Understanding Lock Summary
- **What is being built**: An automated keyword research step executed immediately before the blog generator. It queries Google Trends for related search terms, uses the LLM to filter and select a long-tail, low-competition query, and feeds it directly into the blog generator.
- **Why it exists**: To eliminate manual keyword inputs from the campaign orchestrator and interactive wizard, making campaign creation fully automated.
- **Who it is for**: Campaign operators setting up affiliate traffic funnels.
- **Key constraints**:
  - Must use the `pytrends` library.
  - Must execute autonomously without prompting the user for input.
  - Must estimate "low competition and high search volume" using a combination of Google Trends' relative interest and LLM evaluation (favoring long-tail queries).

---

## ⚙️ 2. Assumptions & Non-Functional Requirements
- **Reliability & Fallback**: `pytrends` requests are subject to rate limiting (HTTP 429) or IP blocks by Google. If a Trends query fails, the system will seamlessly fail-safe by falling back to LLM-guided keyword brainstorming based on the niche.
- **Performance**: The entire keyword discovery step must execute in less than 10-15 seconds.
- **Scale**: Run-on-demand per campaign creation.
- **Security**: No additional API keys are required. Uses the existing `OPENAI_API_KEY` (or `OPENAI_APT_KEY`) for LLM selection.

---

## 🛠️ 3. Decision Log
- **Decision**: Use the unofficial `pytrends` library to fetch search data from Google Trends.
- **Alternatives Considered**: Direct HTTP requests to Google widget endpoints (Approach 1) and Google Search Suggest API (Approach 3).
- **Rationale**: Preferred standard Python library wrapper to manage requests, session payloads, and headers automatically.

---

## 🏗️ 4. Final Design & Component Details

### 1. Dependency Integration (`pyproject.toml`)
Add `pytrends` to the dependency array.

### 2. The Keyword Agent (`src/my_automated_traffic/keyword_agent.py`)
Exposes a `KeywordAgent` class:
- `fetch_trends_queries(niche: str) -> List[str]`:
  - Initializes `TrendReq` from `pytrends.request`.
  - Builds payload for `kw_list=[niche]`.
  - Calls `related_queries()`.
  - Parses the returning dictionary and extracts terms from both `'top'` and `'rising'` DataFrames.
- `select_optimal_keyword(niche: str, queries: List[str]) -> str`:
  - Prompts the LLM with the list of queries.
  - Evaluates search intent and selects the single best SFW long-tail, low-competition keyword.
- `discover_keyword(niche: str) -> str`:
  - Main orchestrator. If `fetch_trends_queries` raises an exception (e.g. rate limit, network fail), it catches it and falls back to LLM brainstorming: *"Brainstorm 10 SFW keywords for {niche} and pick the single best SFW long-tail query."*

### 3. Pipeline Integration (`src/my_automated_traffic/orchestrator.py`)
- The orchestrator will initialize `KeywordAgent` before executing Step 2 (Blog Post).
- The orchestrator will call `agent.discover_keyword(niche)` to retrieve the target keyword.
- The discovered keyword will be stored in the campaign results and passed directly to the `BlogAgent`.

### 4. CLI / Wizard Integration (`src/my_automated_traffic/cli.py`)
- **Option 1 (Add Offer + Run Automation)**: Runs the orchestrator, which automatically executes the keyword agent before generating the blog post. No manual input is asked.
- **Option 2 (Generate Blog Post)**: Instead of prompting `click.prompt("Enter target keyword")`, the CLI will initialize `KeywordAgent`, discover the keyword automatically, report it to the user, and pass it to the `BlogAgent`.
