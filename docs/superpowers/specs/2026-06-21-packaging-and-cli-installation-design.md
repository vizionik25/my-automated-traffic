# Design Spec: CLI Executable Packaging & Installation

## Overview
This document specifies the design for packaging the `my-automated-traffic` project as an installable CLI tool using `uv`. 

## Goals
1. Make the project installable as an executable command `my-automated-traffic` via `uv tool install .`.
2. Create a clean Python entrypoint file `main.py` that handles script invocation.
3. Expose all major classes, CLI commands, and functions inside the package `__init__.py` using a structured `__all__` list.
4. Execute all changes inside a separate git branch.

## Design Details

### 1. Git Isolation
All changes will be developed on a dedicated feature branch:
* **Branch Name**: `feature/installable-cli-tool`
* **Base Branch**: `main`

### 2. File Changes

#### A. New Entrypoint: `src/my_automated_traffic/main.py`
This file serves as the script entry point called by the packaged runner. It imports all modules to ensure they are loaded and declares `main()` which executes the Click CLI interface.

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

#### B. Updated package initialization: `src/my_automated_traffic/__init__.py`
Imports all functions and classes to the top level of the package and defines the `__all__` property.

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

#### C. Console Script Definition: `pyproject.toml`
Ensure the configuration matches:
```toml
[project.scripts]
my-automated-traffic = "my_automated_traffic:main"
```

## Verification Plan
1. Switch back to the newly created branch.
2. Build and install the tool using `uv`:
   ```bash
   uv tool install . --force
   ```
3. Run the CLI to verify it is on the PATH and executable:
   ```bash
   my-automated-traffic --help
   ```
4. Verify package importing works properly:
   ```bash
   python -c "import my_automated_traffic; print(my_automated_traffic.__all__)"
   ```
