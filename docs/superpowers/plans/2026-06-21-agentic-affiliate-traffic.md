# AI-Automated Affiliate Traffic Strategy (NSFW Hybrid Model) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a modular Python CLI agentic suite that automates SEO blogging, short-form video creation, and Reddit/X community replies utilizing SFW pre-lander funnels to drive traffic to NSFW affiliate offers.

**Architecture:** Independent Python agents coordinating through a centralized SQLite database. SFW content (blog, video, social replies) redirects to an interactive pre-lander, which routes users to the target affiliate link.

**Tech Stack:** Python 3.11+, SQLite, Pytest, Jinja2, MoviePy, FFmpeg, Edge-TTS/gTTS, Google GenAI SDK (Gemini)

---

### Task 1: SQLite Database Setup

**Files:**
- Create: `src/database.py`
- Test: `tests/test_database.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_database.py` to assert database initialization and basic operations:
```python
import os
import tempfile
import pytest
from src.database import DatabaseManager

def test_db_initialization():
    temp_db_fd, temp_db_path = tempfile.mkstemp()
    os.close(temp_db_fd)
    
    try:
        db = DatabaseManager(temp_db_path)
        db.initialize()
        
        # Verify tables exist
        tables = db.get_tables()
        assert "offers" in tables
        assert "campaigns" in tables
        assert "blog_posts" in tables
        assert "video_assets" in tables
        assert "social_leads" in tables
        assert "analytics" in tables
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_database.py`
Expected: FAIL with ModuleNotFoundError: No module named 'src.database'

- [ ] **Step 3: Write minimal implementation**

Create `src/database.py`:
```python
import sqlite3

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def initialize(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS offers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    description TEXT,
                    compliance_rules TEXT,
                    niche TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    offer_id INTEGER NOT NULL REFERENCES offers(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'paused',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blog_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
                    keyword TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content_markdown TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'draft',
                    published_url TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
                    script_text TEXT NOT NULL,
                    audio_path TEXT,
                    video_path TEXT,
                    status TEXT NOT NULL DEFAULT 'queued',
                    platform_urls TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS social_leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
                    platform TEXT NOT NULL,
                    thread_id TEXT NOT NULL,
                    thread_title_or_content TEXT,
                    reply_content TEXT,
                    status TEXT NOT NULL DEFAULT 'scraped',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(platform, thread_id)
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
                    platform TEXT NOT NULL,
                    clicks INTEGER DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    conversions INTEGER DEFAULT 0,
                    recorded_date DATE NOT NULL UNIQUE
                );
            """)
            conn.commit()

    def get_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            return [row[0] for row in cursor.fetchall()]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_database.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/database.py tests/test_database.py
git commit -m "feat: implement SQLite database initialization and schema"
```

---

### Task 2: Database Operations for Campaigns and Offers

**Files:**
- Modify: `src/database.py`
- Test: `tests/test_database.py`

- [ ] **Step 1: Write the failing test**

Add tests for adding offers, creating campaigns, and logging activities to `tests/test_database.py`:
```python
def test_create_offer_and_campaign():
    temp_db_fd, temp_db_path = tempfile.mkstemp()
    os.close(temp_db_fd)
    
    try:
        db = DatabaseManager(temp_db_path)
        db.initialize()
        
        offer_id = db.add_offer("http://offer.com", "Adult Dating Niche", "No email spam", "dating")
        assert offer_id == 1
        
        campaign_id = db.add_campaign(offer_id, "Summer Dating Campaign")
        assert campaign_id == 1
        
        campaigns = db.get_active_campaigns()
        assert len(campaigns) == 0  # Starts as paused
        
        db.update_campaign_status(campaign_id, "active")
        active_campaigns = db.get_active_campaigns()
        assert len(active_campaigns) == 1
        assert active_campaigns[0][2] == "Summer Dating Campaign"
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_database.py::test_create_offer_and_campaign`
Expected: FAIL with AttributeError (methods not defined)

- [ ] **Step 3: Write minimal implementation**

Add methods to `DatabaseManager` in `src/database.py`:
```python
    def add_offer(self, url, description, compliance_rules, niche):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO offers (url, description, compliance_rules, niche) VALUES (?, ?, ?, ?)",
                (url, description, compliance_rules, niche)
            )
            conn.commit()
            return cursor.lastrowid

    def add_campaign(self, offer_id, name):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO campaigns (offer_id, name) VALUES (?, ?)",
                (offer_id, name)
            )
            conn.commit()
            return cursor.lastrowid

    def update_campaign_status(self, campaign_id, status):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE campaigns SET status = ? WHERE id = ?",
                (status, campaign_id)
            )
            conn.commit()

    def get_active_campaigns(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, offer_id, name, status FROM campaigns WHERE status = 'active'")
            return cursor.fetchall()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_database.py::test_create_offer_and_campaign`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/database.py tests/test_database.py
git commit -m "feat: add CRUD operations for offers and campaigns in database"
```

---

### Task 3: Interactive SFW Bridge Landing Page Engine

**Files:**
- Create: `src/bridge_page.py`
- Test: `tests/test_bridge_page.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_bridge_page.py`:
```python
import os
import tempfile
import pytest
from src.bridge_page import QuizPageGenerator

def test_quiz_generation():
    temp_dir = tempfile.mkdtemp()
    try:
        generator = QuizPageGenerator(temp_dir)
        output_file = generator.generate(
            title="Dating Blueprint Quiz",
            offer_url="http://nsfw-offer.com",
            niche="dating"
        )
        assert os.path.exists(output_file)
        with open(output_file, 'r') as f:
            content = f.read()
            assert "Dating Blueprint Quiz" in content
            assert "http://nsfw-offer.com" in content
            assert "confirmRedirect" in content
    finally:
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_bridge_page.py`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Write minimal implementation**

Create `src/bridge_page.py`:
```python
import os

class QuizPageGenerator:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate(self, title, offer_url, niche):
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; background-color: #fafafa; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
        .card {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; max-width: 400px; }}
        button {{ background: #4f46e5; color: white; border: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="card">
        <h2>{title}</h2>
        <p>Complete this simple test to reveal your custom relationship compatibility profile.</p>
        <button id="cta-button" onclick="confirmRedirect()">Begin Assessment</button>
    </div>
    <script>
        function confirmRedirect() {{
            const consent = confirm("You are about to be redirected. You must be over 18 to proceed. Do you agree?");
            if (consent) {{
                window.location.href = "{offer_url}";
            }}
        }}
    </script>
</body>
</html>
"""
        filename = f"{niche}_quiz.html"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(html_content)
        return filepath
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_bridge_page.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/bridge_page.py tests/test_bridge_page.py
git commit -m "feat: implement Jinja-style SFW bridge page quiz generator"
```

---

### Task 4: SFW SEO Blog Generator Agent

**Files:**
- Create: `src/blog_agent.py`
- Test: `tests/test_blog_agent.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_blog_agent.py` targeting LLM generation mockup:
```python
import pytest
from unittest.mock import MagicMock
from src.blog_agent import BlogAgent

def test_blog_post_generation():
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "Mocked helpful SFW relationship advice blog post content."
    
    agent = BlogAgent(llm_client=mock_llm)
    post = agent.generate_post(
        keyword="how to start a conversation with a girl",
        niche="dating",
        bridge_url="http://localhost:8000/dating_quiz.html"
    )
    
    assert post["keyword"] == "how to start a conversation with a girl"
    assert "dating" in post["title"].lower() or "conversation" in post["title"].lower()
    assert "Mocked helpful SFW" in post["content"]
    assert "http://localhost:8000/dating_quiz.html" in post["content"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_blog_agent.py`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Write minimal implementation**

Create `src/blog_agent.py`:
```python
class BlogAgent:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def generate_post(self, keyword, niche, bridge_url):
        # Request content from LLM
        prompt = f"Write a SFW relationship blog post about: '{keyword}'. Soft pitch this quiz link at the end: {bridge_url}."
        generated_content = self.llm_client.generate(prompt)
        
        title = f"Dating & Relationships: {keyword.capitalize()}"
        content = f"""# {title}

{generated_content}

---
Need personalized tips? Take our interactive [Dating & Relationship Quiz]({bridge_url}) to find your styling blueprint.
"""
        return {
            "keyword": keyword,
            "title": title,
            "content": content
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_blog_agent.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/blog_agent.py tests/test_blog_agent.py
git commit -m "feat: implement Blog SEO Agent content generation"
```

---

### Task 5: SFW Short-form Video Creator Agent

**Files:**
- Create: `src/video_agent.py`
- Test: `tests/test_video_agent.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_video_agent.py` asserting script generation and media generation logic (with audio generation mocked to stay platform independent):
```python
import os
import pytest
from unittest.mock import MagicMock
from src.video_agent import VideoAgent

def test_video_script_draft():
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "Hook: Want to know if she likes you? \nBody: Check if she leans in when talking. \nCTA: Click link in bio to test your score."
    
    agent = VideoAgent(llm_client=mock_llm)
    script = agent.generate_script(niche="dating")
    
    assert "Hook:" in script
    assert "CTA:" in script
    
def test_tts_generation(tmp_path):
    mock_llm = MagicMock()
    agent = VideoAgent(llm_client=mock_llm)
    
    audio_file = os.path.join(tmp_path, "test.mp3")
    agent.generate_audio("Hello World from TTS", audio_file)
    assert os.path.exists(audio_file)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_video_agent.py`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Write minimal implementation**

Create `src/video_agent.py` wrapping standard TTS (`gtts`):
```python
import os
from gtts import gTTS

class VideoAgent:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def generate_script(self, niche):
        prompt = f"Write a short, engaging 30-second TikTok script about {niche} advice. Must contain 'Hook:', 'Body:', and 'CTA: link in bio'."
        return self.llm_client.generate(prompt)

    def generate_audio(self, text, output_path):
        tts = gTTS(text=text, lang='en')
        tts.save(output_path)
        return output_path
```

- [ ] **Step 4: Run test to verify it passes**

Make sure `gtts` is installed (`pip install gTTS`).
Run: `pytest tests/test_video_agent.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/video_agent.py tests/test_video_agent.py
git commit -m "feat: implement Video Creator Agent script drafting and TTS"
```

---

### Task 6: Social Monitoring and Reply Agent

**Files:**
- Create: `src/social_agent.py`
- Test: `tests/test_social_agent.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_social_agent.py` testing conversation filtering and response generation:
```python
import pytest
from unittest.mock import MagicMock
from src.social_agent import SocialAgent

def test_filter_and_reply():
    mock_llm = MagicMock()
    # Mocking two replies: first for is_relevant (should return Yes/No), second for reply_content
    mock_llm.generate.side_effect = ["Yes", "Try starting with a warm smile and asking about her day."]
    
    agent = SocialAgent(llm_client=mock_llm)
    thread = {
        "id": "t1_abc",
        "title": "I am too scared to talk to girls, how do I start a conversation?",
        "content": "Every time I see someone I like, I freeze up. Help!"
    }
    
    is_relevant = agent.is_relevant(thread, niche="dating")
    assert is_relevant is True
    
    reply = agent.generate_reply(thread, ref_blog_url="http://blog.com/dating-tips")
    assert "smile" in reply
    assert "http://blog.com/dating-tips" in reply
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_social_agent.py`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Write minimal implementation**

Create `src/social_agent.py`:
```python
class SocialAgent:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def is_relevant(self, thread, niche):
        prompt = f"Does the following thread discuss advice queries relating to '{niche}'? Respond only with Yes or No.\n\nTitle: {thread['title']}\nContent: {thread['content']}"
        response = self.llm_client.generate(prompt)
        return response.strip().lower() == "yes"

    def generate_reply(self, thread, ref_blog_url):
        prompt = f"Write a helpful, empathetic SFW response to this thread: '{thread['title']}'. Do not spam. Softly reference this resource link: {ref_blog_url}."
        advice = self.llm_client.generate(prompt)
        return f"{advice}\n\nFor more detail, check out: {ref_blog_url}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_social_agent.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/social_agent.py tests/test_social_agent.py
git commit -m "feat: implement Reddit/X Monitoring Agent matching and replies"
```

---

### Task 7: Command Line Interface (CLI) Orchestrator

**Files:**
- Create: `src/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_cli.py` to test basic entrypoints and command handling:
```python
import os
import tempfile
import pytest
from click.testing import CliRunner
from src.cli import main_cli

def test_cli_add_offer():
    temp_db_fd, temp_db_path = tempfile.mkstemp()
    os.close(temp_db_fd)
    
    try:
        runner = CliRunner()
        result = runner.invoke(main_cli, [
            "--db-path", temp_db_path,
            "add-offer",
            "--url", "http://offer.com",
            "--desc", "Adult dating hook",
            "--rules", "No spamming",
            "--niche", "dating"
        ])
        assert result.exit_code == 0
        assert "Successfully added offer" in result.output
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Write minimal implementation**

Create `src/cli.py` using click:
```python
import click
from src.database import DatabaseManager

@click.group()
@click.option('--db-path', default='campaigns.db', help='Path to SQLite database')
@click.pass_context
def main_cli(ctx, db_path):
    ctx.ensure_object(dict)
    ctx.obj['db'] = DatabaseManager(db_path)
    ctx.obj['db'].initialize()

@main_cli.command()
@click.option('--url', required=True)
@click.option('--desc', default='')
@click.option('--rules', default='')
@click.option('--niche', required=True)
@click.pass_context
def add_offer(ctx, url, desc, rules, niche):
    db = ctx.obj['db']
    offer_id = db.add_offer(url, desc, rules, niche)
    click.echo(f"Successfully added offer with ID: {offer_id}")

if __name__ == '__main__':
    main_cli(obj={})
```

- [ ] **Step 4: Run test to verify it passes**

Make sure `click` is installed (`pip install click`).
Run: `pytest tests/test_cli.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/cli.py tests/test_cli.py
git commit -m "feat: implement Unified CLI runner configuration"
```
