# Design Spec: Interactive CLI Wizard

## Overview
This spec outlines the addition of an interactive menu-driven wizard to `my-automated-traffic`. When the user runs the tool without arguments/subcommands, the tool will start the wizard loop.

## Goals
1. Detect invocation without subcommands/arguments.
2. Launch a menu loop supporting:
   * Adding affiliate offers.
   * Creating campaigns.
   * Generating blog posts (`BlogAgent`).
   * Generating bridge pages (`QuizPageGenerator`).
   * Generating video scripts & videos (`VideoAgent`).
   * Managing social leads (`SocialAgent`).
3. Maintain CLI backward compatibility for direct automated commands.

## Design Details

### 1. Git Isolation
* **Branch Name**: `feature/interactive-cli-wizard`
* **Base Branch**: `main`

### 2. Mock LLM Client
To run LLM-based agent code without external API dependencies, `cli.py` will include a `MockLLMClient` class that returns dynamic responses based on the prompts:
```python
class MockLLMClient:
    """Mock LLM Client generating realistic stub outputs for agent tests/wizard runs."""
    def generate(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if "tiktok script" in prompt_lower or "tiktok" in prompt_lower:
            return (
                "Hook: Stop making these relationship mistakes!\n"
                "Body: Focus on communication, validation, and growing together.\n"
                "CTA: link in bio"
            )
        elif "relationship advice script" in prompt_lower:
            return (
                '{\n'
                '  "scenes": [\n'
                '    {"scene_number": 1, "voiceover_text": "Stop making dating mistakes.", "visual_prompt": "Cinematic couple laughing, warm lighting, SFW"},\n'
                '    {"scene_number": 2, "voiceover_text": "Take our quiz today.", "visual_prompt": "Phone screen displaying quiz, soft ambient background, SFW"}\n'
                '  ]\n'
                '}'
            )
        elif "blog post" in prompt_lower:
            return (
                "Here are key dating and relationship tips. Communication is key to bonding. "
                "Understanding your partner's values helps navigate style compatibility."
            )
        elif "discuss advice queries" in prompt_lower:
            return "Yes"
        elif "response to this thread" in prompt_lower:
            return "That sounds like a tough situation. Try talking things out openly and see how they feel."
        return "Standard mock LLM generation for prompt: " + prompt
```

### 3. CLI Changes (`src/my_automated_traffic/cli.py`)
Modify `main_cli` to check if a subcommand has been invoked:
```python
@click.group()
@click.option('--db-path', default='campaigns.db', help='Path to SQLite database')
@click.pass_context
def main_cli(ctx: click.Context, db_path: str) -> None:
    ctx.ensure_object(dict)
    db = DatabaseManager(db_path)
    db.initialize()
    ctx.obj['db'] = db
    
    if ctx.invoked_subcommand is None:
        run_interactive_wizard(ctx)
```

The `run_interactive_wizard(ctx)` loop will run:
```python
def run_interactive_wizard(ctx: click.Context) -> None:
    """Runs the main menu loop for interactive wizard."""
    db: DatabaseManager = ctx.obj['db']
    llm_client = MockLLMClient()

    while True:
        click.echo("\n==========================================")
        click.echo("       AFFILIATE STRATEGY WIZARD")
        click.echo("==========================================")
        click.echo("1. Add a New Affiliate Offer")
        click.echo("2. Create a Campaign")
        click.echo("3. Generate Blog Post (BlogAgent)")
        click.echo("4. Generate Bridge Page (QuizPageGenerator)")
        click.echo("5. Generate Video Asset (VideoAgent)")
        click.echo("6. Manage Social Leads (SocialAgent)")
        click.echo("7. Exit")
        click.echo("==========================================")
        
        choice = click.prompt("Select an option (1-7)", type=int, default=7)
        
        if choice == 1:
            # Add Affiliate Offer
            url = click.prompt("Enter offer URL")
            desc = click.prompt("Enter description", default="")
            rules = click.prompt("Enter compliance rules", default="")
            niche = click.prompt("Enter niche")
            offer_id = db.add_offer(url, desc, rules, niche)
            click.echo(f"Successfully added offer with ID: {offer_id}")
            
        elif choice == 2:
            # Create Campaign
            # Fetches existing offers...
            # Prompts for offer ID and campaign name...
            # Saves campaign to DB
            ...
            
        elif choice == 3:
            # Generate Blog Post
            ...
            
        elif choice == 4:
            # Generate Bridge Page
            ...
            
        elif choice == 5:
            # Generate Video Asset
            ...
            
        elif choice == 6:
            # Manage Social Leads
            ...
            
        elif choice == 7:
            click.echo("Exiting wizard. Goodbye!")
            break
```

## Verification Plan
1. Switch to branch `feature/interactive-cli-wizard`.
2. Run `my-automated-traffic` with no arguments.
3. Test each wizard menu option (1 through 7) to verify functionality.
4. Verify standard subcommand invocation (e.g., `my-automated-traffic add-offer ...`) still bypasses the wizard and executes directly.
5. Verify test suite (`pytest`) runs successfully.
