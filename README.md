# my-automated-traffic

An AI-driven traffic generation suite that automates content creation and social marketing campaigns. The project operates on a **Hybrid SFW-to-NSFW Bridge Funnel** model: safe-for-work (SFW) traffic generation channels capture interest, drive users to an interactive SFW pre-lander (quiz gate), verify user consent, and direct high-intent traffic to target affiliate offers.

---

## 💡 System Architecture & Core Concept

Traffic is generated from SFW channels and routed through a consent gate before forwarding users to affiliate offers:

```
[ SFW Traffic Sources ]
 ├── Video Agent   ──► (TikTok / Shorts vertical videos)  ──► [ SFW Bridge Page / Quiz ]
 ├── Blog Agent    ──► (SEO advice articles)              ──►          │
 └── Social Agent  ──► (Reddit / X advice forum replies)  ──►          ▼
                                                              [ Consent & 18+ Verification ]
                                                                           │
                                                                           ▼
                                                              [ Target Affiliate Offer ]
```

All campaigns, assets, and operational stats are tracked locally in a centralized SQLite database.

---

## 🛠️ Project Requirements & Prerequisites

- **Python**: version `>=3.14` (as defined in `pyproject.toml`)
- **Package Manager**: [uv](https://github.com/astral-sh/uv) (Fast Python package resolver and installer)
- **External Dependencies**:
  - **FFmpeg**: Required by `moviepy` for rendering video and audio tracks.
    - *macOS*: `brew install ffmpeg`
    - *Linux*: `sudo apt-get install ffmpeg`
    - *Windows*: Download binaries from official channels and add them to your system's `PATH`.

---

## 🚀 Installation & Virtual Environment Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/vizionik25/my-automated-traffic.git
   cd my-automated-traffic
   ```

2. **Sync Virtual Environment**:
   Initialize and synchronize the environment dependencies using `uv`:
   ```bash
   uv sync
   ```
   This automatically installs the virtual environment and packages compiled inside `pyproject.toml`.

---

## ⚙️ Configuration & Environment Variables

The suite integrates with any OpenAI-compatible API endpoint (such as OpenAI, OpenRouter, LM Studio, Ollama, etc.) for language modeling tasks. Set the following environment variables prior to running the commands:

```bash
export OPENAI_API_BASE="https://api.openai.com/v1"   # API endpoint URL
export OPENAI_API_KEY="sk-your-key-here"            # Your API authorization key
export OPENAI_MODEL="gpt-4o-mini"                  # Model identifier (optional; defaults to gpt-4o-mini)
```

---

## 📖 Command Line Interface (CLI) & Interactive Wizard

The application compiles into an installable command-line interface. Run it via `uv` or call the console script directly.

### 1. Launching the Interactive Wizard
Running the package executable without subcommands starts the interactive wizard:

```bash
uv run my-automated-traffic
```

The wizard provides a step-by-step menu to perform all core tasks:
```
==========================================
       AFFILIATE STRATEGY WIZARD
==========================================
1. Add a New Affiliate Offer (+ Run Automation)
2. Generate Blog Post (BlogAgent)
3. Generate Bridge Page (QuizPageGenerator)
4. Generate Video Asset (VideoAgent)
5. Manage Social Leads (SocialAgent)
6. Exit
==========================================
```

Selecting option **1. Add a New Affiliate Offer (+ Run Automation)** allows you to input offer details, insert them into the database, create a campaign, and run the automated bridge page, blog post, and vertical video compilation sequence. A detailed deployment instruction file (`REPORT.md`) is written to your output directory upon completion.

---

### 2. Click CLI Subcommands

Alternatively, run specific actions using CLI subcommands:

#### Add an Affiliate Offer
Adds a new affiliate link to the database:
```bash
uv run my-automated-traffic add-offer \
  --url "https://target-affiliate-link.com" \
  --desc "Offer description here" \
  --rules "Promo constraints" \
  --niche "dating"
```

#### Generate a Social Media Reply
Validates a forum thread for niche relevance and drafts a SFW reply containing your blog URL:
```bash
uv run my-automated-traffic social-reply \
  --niche "dating" \
  --thread-title "How do I approach someone at a bookstore?" \
  --thread-content "I see this cute girl reading every Saturday and..." \
  --blog-url "https://myblog.com/approaching-tips" \
  --platform "Reddit"
```

---

## 🤖 Overview of Traffic Generation Agents

For exhaustive specifications on how each agent functions, see the [Specialized Traffic Generation Agents](file:///Users/vizionik/AffiliateStrategy/docs/AGENTS.md) guide.

- **Quiz Pre-lander Generator** ([QuizPageGenerator](file:///Users/vizionik/AffiliateStrategy/src/my_automated_traffic/bridge_page.py)): Compiles standalone, responsive HTML landing pages equipped with age-gate verification prompts and redirection scripts.
- **SEO Blog Writer** ([BlogAgent](file:///Users/vizionik/AffiliateStrategy/src/my_automated_traffic/blog_agent.py)): Research-driven SEO content generator targeting niche keywords and embedding call-to-actions pointing to the quiz gate.
- **Subtitled Video Compositor** ([VideoAgent](file:///Users/vizionik/AffiliateStrategy/src/my_automated_traffic/video_agent.py)): Scriptwriter and video composite engine. It handles text-to-speech synthesis (using `edge-tts` for precise word-highlight timing), background image synthesis (using `imagen` or native Pillow gradients), Ken Burns zoom transitions, logo placement, and final video rendering.
- **Forum Response Manager** ([SocialAgent](file:///Users/vizionik/AffiliateStrategy/src/my_automated_traffic/social_agent.py)): Relevance classifier and empathetic response drafting engine targeting community threads on Reddit or X.

---

## 🗄️ Database Management & Schema

The sqlite database schema tracks relationships between campaigns, offers, blog posts, video assets, scraped threads, and conversion metrics. Review the full schema and column definitions in the [Database Schema & Data Models](file:///Users/vizionik/AffiliateStrategy/docs/DATABASE.md) specification.

---

## 🧪 Verification & Running Tests

Unit tests are written using `pytest`. Mocks isolate the test environment from external API calls (LLM client, edge-tts synthesis, image calls) to ensure execution remains local and fast.

Run the test suite:
```bash
uv run pytest
```
