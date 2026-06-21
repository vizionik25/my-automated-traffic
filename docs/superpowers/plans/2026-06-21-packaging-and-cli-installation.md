# CLI Executable Packaging & Installation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package the Affiliate Strategy project so it can be installed via `uv tool install` and expose all functions/classes properly via `__init__.py`.

**Architecture:** Create a `main.py` entrypoint invoking the Click CLI, expose all classes and CLI functions at the package root level in `__init__.py` using `__all__`, and verify local installation.

**Tech Stack:** Python 3.14+, uv, Click.

---

### Task 1: Create main.py Entrypoint

**Files:**
- Create: `src/my_automated_traffic/main.py`

- [ ] **Step 1: Create the main.py entrypoint file**
  Create the entrypoint file that imports all package components and executes the Click CLI.
  
  ```python
  from my_automated_traffic.blog_agent import BlogAgent
  from my_automated_traffic.bridge_page import QuizPageGenerator
  from my_automated_traffic.cli import main_cli, add_offer
  from my_automated_traffic.database import DatabaseManager
  from my_automated_traffic.social_agent import SocialAgent
  from my_automated_traffic.video_agent import VideoAgent

  def main() -> None:
      """Console script entrypoint function."""
      main_cli(obj={})

  if __name__ == "__main__":
      main()
  ```

- [ ] **Step 2: Commit the changes**
  Run:
  ```bash
  git add src/my_automated_traffic/main.py
  git commit -m "feat: add main.py script entrypoint"
  ```

---

### Task 2: Update Package Initializer __init__.py

**Files:**
- Modify: `src/my_automated_traffic/__init__.py`

- [ ] **Step 1: Update package __init__.py with all imports and __all__ guard**
  Replace the contents of `src/my_automated_traffic/__init__.py` to import all agent, database, CLI, and main entrypoint functions, setting the `__all__` list.

  ```python
  from my_automated_traffic.blog_agent import BlogAgent
  from my_automated_traffic.bridge_page import QuizPageGenerator
  from my_automated_traffic.cli import main_cli, add_offer
  from my_automated_traffic.database import DatabaseManager
  from my_automated_traffic.main import main
  from my_automated_traffic.social_agent import SocialAgent
  from my_automated_traffic.video_agent import VideoAgent

  __all__ = [
      "BlogAgent",
      "QuizPageGenerator",
      "main_cli",
      "add_offer",
      "DatabaseManager",
      "main",
      "SocialAgent",
      "VideoAgent",
  ]
  ```

- [ ] **Step 2: Commit the changes**
  Run:
  ```bash
  git add src/my_automated_traffic/__init__.py
  git commit -m "feat: import and expose all modules in package __init__"
  ```

---

### Task 3: Local CLI Installation and Verification

**Files:**
- None (verification task)

- [ ] **Step 1: Install tool locally via uv**
  Run: `uv tool install . --force`
  Expected output should contain: `Installed my-automated-traffic`

- [ ] **Step 2: Test the executable command from the shell**
  Run: `my-automated-traffic --help`
  Expected: Click CLI help output showing options (`--db-path`) and commands (`add-offer`).

- [ ] **Step 3: Test package importing and __all__ guard**
  Run: `python -c "import my_automated_traffic; print(my_automated_traffic.__all__)"`
  Expected: Output showing the list of exposed classes and functions: `['BlogAgent', 'QuizPageGenerator', 'main_cli', 'add_offer', 'DatabaseManager', 'main', 'SocialAgent', 'VideoAgent']`
