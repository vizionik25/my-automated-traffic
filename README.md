# AI-Automated Affiliate Strategy Campaign Suite

An AI-driven traffic generation suite designed to automate content creation and social marketing campaigns. The project utilizes a **Hybrid SFW Bridge Funnel** strategy: SFW traffic channels (Blogging, Short-form Videos, Reddit/X advice replies) capture attention and drive users to an interactive SFW pre-lander (quiz/landing gate), which performs age/consent verification before routing users to the target affiliate offer.

---

## 💡 System Architecture

```
[ SFW Traffic Sources ]
 ├── Video Creator Agent   ──► (TikTok / Shorts / Reels videos) ──► [ SFW Bridge Page / Quiz ]
 ├── SEO Blog Agent        ──► (Helpful advice articles)        ──►          │
 └── Social Monitor Agent  ──► (Reddit / X thread replies)      ──►          ▼
                                                                [ Consent & Age Verification ]
                                                                             │
                                                                             ▼
                                                                [ Target Affiliate Offer ]
```

All agent activities, campaign configurations, and performance statistics coordinate locally through a centralized SQLite database.

---

## 🛠️ Tech Stack & Key Libraries

* **Package Manager**: [uv](https://github.com/astral-sh/uv) (Fast Python dependency installer and resolver)
* **LLM Engine**: Google GenAI SDK (Gemini) / OpenAI compatible client
* **Speech Synthesis**: [edge-tts](https://github.com/rany2/edge-tts) (High-quality voiceovers with precise word timings)
* **Image Generation**: Google GenAI Imagen (with dynamic Pillow fallback)
* **Video Rendering**: [MoviePy](https://github.com/Zulko/moviepy) & [Pillow](https://github.com/python-pillow/Pillow) (ImageMagick-free caption rendering, logo watermarking, Ken Burns effects, and stitching)
* **Database**: SQLite3

---

## 🚀 Getting Started

### Prerequisites

1. **Python 3.11+** (Python 3.14 recommended, managed via `uv`)
2. **FFmpeg** installed on your system PATH (required by MoviePy for writing video and audio tracks)
   * *macOS*: `brew install ffmpeg`
   * *Linux*: `sudo apt install ffmpeg`
   * *Windows*: Install via Chocolatey or download directly and add to Environment variables.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/vizionik25/my-automated-traffic.git
   cd my-automated-traffic
   ```

2. Initialize and sync the python virtual environment using `uv`:
   ```bash
   uv sync
   ```

---

## 📖 Usage Guide

### 1. Database & CLI Operations
The orchestrator is exposed via a Click Command Line Interface. Initialize the SQLite database and manage campaigns directly from your terminal:

* **Add an Affiliate Offer**:
  ```bash
  uv run python src/my_automated_traffic/cli.py add-offer --url "https://target-affiliate-link.com" --desc "Niche offer description" --rules "Compliance guidelines" --niche "dating"
  ```

---

## 🤖 Specialized Agents

### 🎥 SFW Video Creator Agent (`VideoAgent`)
Generates high-engagement vertical short-form videos with automatic captioning and brand watermarks.
* **Script Generation**: Calls Gemini to output a structured JSON script (divided into Hook, Body, and CTA scenes).
* **Audio Voiceover**: Uses Microsoft Edge-TTS to synthesize speech and parse precise word boundary timestamps.
* **AI Image Generation**: Call Google Imagen to create custom 9:16 vertical background images for each scene. (Pillow color-gradients act as fallbacks if the API is unavailable).
* **Composition & Overlay**: Pre-renders word-highlighted subtitle frames using Pillow (avoiding external ImageMagick binaries) and stitches them using MoviePy with Ken Burns pan/zoom animations, logo watermarks, and promotional deliverables.

### ✍️ SFW SEO Blog Generator Agent (`BlogAgent`)
Drafts SEO-optimized blog posts around question keywords.
* **Workflow**: LLM generates 1,000+ words of helpful advice and naturally embeds CTAs linking to the campaign's interactive quiz pre-lander.

### 💬 Reddit/X Reply Monitoring Agent (`SocialAgent`)
Monitors social advice threads to identify high-intent queries and automatically drafts answers.
* **Workflow**: Scrapes threads matching the niche, filters for relevance, and writes a SFW, highly valuable response referencing a blog article link for further reading.

### ✨ SFW Bridge Page Quiz Generator (`QuizPageGenerator`)
Generates lightweight HTML quiz pages that serve as compliance gateways. Includes age checks and redirects users to target offers upon completion.

---

## 🧪 Running Tests

The project utilizes `pytest` to assert behavior across the database, CLI, and all specialized agents. Network calls (LLM client, Imagen, edge-tts) are fully mocked out to ensure test suite execution remains fast and self-contained.

Run the test suite:
```bash
uv run pytest
```
