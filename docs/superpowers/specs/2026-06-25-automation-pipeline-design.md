# Automation Pipeline Design Spec

## Overview

When a user adds an offer via the interactive wizard, the system automatically:
1. Prompts for a campaign name
2. Creates the campaign in the database
3. Runs all content agents sequentially (Bridge Page → Blog Post → Video)
4. Saves all outputs to `output/<campaign-name>/` with subdirectories
5. Generates a markdown report with file locations, deployment instructions, and SocialAgent usage docs

## Components

### 1. Real LLM Client (`llm_client.py`)

Replaces `MockLLMClient` entirely. Uses the `openai` Python SDK to hit any OpenAI-compatible endpoint.

**Environment Variables:**
- `OPENAI_API_BASE` (required) — API endpoint URL
- `OPENAI_API_KEY` (required) — API key
- `OPENAI_MODEL` (optional, default: `gpt-4o-mini`) — Model identifier

**Interface:**
- `generate(prompt: str) -> str` — matches existing `LLMClient` Protocol
- Raises `EnvironmentError` on instantiation if required env vars are missing

### 2. Pipeline Orchestrator (`orchestrator.py`)

Orchestrates the full content generation pipeline.

**Class: `PipelineOrchestrator`**

Constructor args:
- `llm_client: LLMClient` — the real LLM client
- `db: DatabaseManager` — database manager instance
- `base_output_dir: str` — defaults to `"output"`

**Method: `run(offer_id: int, campaign_name: str) -> str`**

Returns the path to the generated markdown report.

**Execution order:**
1. Fetch offer details from DB (url, niche, description)
2. Create campaign in DB
3. Create output directory structure: `output/<campaign-name>/bridge/`, `output/<campaign-name>/blog/`, `output/<campaign-name>/video/`
4. **Step 1 — Bridge Page:** Generate quiz bridge page HTML using `QuizPageGenerator`
5. **Step 2 — Blog Post:** Generate blog post using `BlogAgent`, save as `.md` file. Uses bridge page path as the link.
6. **Step 3 — Video:** Generate video using `VideoAgent` (script → voiceover → images → compose)
7. **Step 4 — Report:** Generate markdown report summarizing everything
8. Print progress to terminal at each step

### 3. Report Generator (inside `orchestrator.py`)

**Method: `_generate_report(...)` -> str**

Generates a markdown file at `output/<campaign-name>/REPORT.md` containing:

- Campaign metadata (name, offer URL, niche, creation timestamp)
- Generated assets table (type, filename, file path)
- Bridge page deployment instructions (upload to hosting, configure domain)
- Blog post deployment instructions (publish to CMS/WordPress)
- Video deployment instructions (upload to TikTok/YouTube Shorts/Reels)
- SocialAgent manual usage instructions (CLI command, what it does, example)
- Environment setup reference (env vars needed)

### 4. CLI Updates (`cli.py`)

- **Delete** `MockLLMClient` class entirely
- **Add** `from my_automated_traffic.llm_client import OpenAIClient`
- **Add** `from my_automated_traffic.orchestrator import PipelineOrchestrator`
- **Update** wizard menu option 1 ("Add a New Affiliate Offer"):
  - After collecting offer details and saving to DB
  - Prompt for campaign name
  - Instantiate `OpenAIClient()` (will error if env vars missing)
  - Instantiate `PipelineOrchestrator(llm_client, db)`
  - Call `orchestrator.run(offer_id, campaign_name)`
  - Display report path on completion
- **Update** all other wizard menu options (3-6) to use `OpenAIClient()` instead of `MockLLMClient()`
- **Remove** menu option 2 ("Create a Campaign") — campaigns are now auto-created during the pipeline

### 5. Package Updates

- **`pyproject.toml`**: Add `openai` to dependencies
- **`__init__.py`**: Export `OpenAIClient` and `PipelineOrchestrator`

## Output Directory Structure

```
output/
└── my-campaign/
    ├── bridge/
    │   └── relationships_quiz.html
    ├── blog/
    │   └── blog_post.md
    ├── video/
    │   └── output.mp4
    └── REPORT.md
```

## Error Handling

- Missing env vars → `EnvironmentError` with clear message listing what to set
- Individual agent failures → caught, logged, pipeline continues with remaining agents. Report notes which steps failed.
- All agents fail → report still generated listing failures

## No Mock Policy

There is NO mock client, NO fallback, NO fake data anywhere in the system. Every LLM call goes through the real OpenAI-compatible API.
