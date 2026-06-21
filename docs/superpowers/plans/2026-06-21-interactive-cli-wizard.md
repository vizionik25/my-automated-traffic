# Interactive CLI Wizard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create an interactive wizard menu in `cli.py` that executes when the command-line tool is run without arguments.

**Architecture:** Update `cli.py` to check if a subcommand was specified. If not, instantiate `MockLLMClient` and run an interactive prompt menu loop. Support all 6 agent/data workflows in the wizard.

**Tech Stack:** Python 3.14+, uv, Click, asyncio.

---

### Task 1: Update cli.py with MockLLMClient and run_interactive_wizard

**Files:**
- Modify: `src/my_automated_traffic/cli.py`

- [ ] **Step 1: Write the updated implementation for cli.py**
  Add `MockLLMClient`, import agents, add `import asyncio`, and implement `run_interactive_wizard(ctx)` helper. Update `main_cli` to invoke it when no subcommand is specified.

  ```python
  import click
  import os
  import asyncio
  from typing import Dict, Any, List
  
  from my_automated_traffic.database import DatabaseManager
  from my_automated_traffic.blog_agent import BlogAgent
  from my_automated_traffic.bridge_page import QuizPageGenerator
  from my_automated_traffic.social_agent import SocialAgent
  from my_automated_traffic.video_agent import VideoAgent

  class MockLLMClient:
      """Mock LLM Client generating realistic outputs for testing and wizard runs."""
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

  def run_interactive_wizard(ctx: click.Context) -> None:
      """Runs the main interactive wizard menu."""
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
              url = click.prompt("Enter offer URL")
              if not (url.startswith("http://") or url.startswith("https://")):
                  click.echo("Error: URL must start with http:// or https://")
                  continue
              desc = click.prompt("Enter description", default="")
              rules = click.prompt("Enter compliance rules", default="")
              niche = click.prompt("Enter niche")
              offer_id = db.add_offer(url, desc, rules, niche)
              click.echo(f"Successfully added offer with ID: {offer_id}")
              
          elif choice == 2:
              # Get all offers
              with db.get_connection() as conn:
                  cursor = conn.cursor()
                  cursor.execute("SELECT id, url, niche FROM offers")
                  offers = cursor.fetchall()
              if not offers:
                  click.echo("No offers available. Please add an offer first.")
                  continue
              click.echo("\nAvailable Offers:")
              for o in offers:
                  click.echo(f"ID: {o['id']} | Niche: {o['niche']} | URL: {o['url']}")
              offer_id = click.prompt("Enter Offer ID", type=int)
              name = click.prompt("Enter Campaign Name")
              try:
                  campaign_id = db.add_campaign(offer_id, name)
                  click.echo(f"Successfully created campaign with ID: {campaign_id}")
              except Exception as e:
                  click.echo(f"Error creating campaign: {e}")
              
          elif choice == 3:
              keyword = click.prompt("Enter target keyword")
              niche = click.prompt("Enter niche")
              bridge_url = click.prompt("Enter bridge URL")
              agent = BlogAgent(llm_client)
              post = agent.generate_post(keyword, niche, bridge_url)
              click.echo("\n--- Generated Blog Post ---")
              click.echo(f"Title: {post['title']}")
              click.echo(f"Content:\n{post['content']}")
              click.echo("---------------------------")
              
          elif choice == 4:
              title = click.prompt("Enter bridge page title")
              offer_url = click.prompt("Enter offer URL")
              niche = click.prompt("Enter niche")
              output_dir = click.prompt("Enter output directory", default=".")
              generator = QuizPageGenerator(output_dir)
              try:
                  filepath = generator.generate(title, offer_url, niche)
                  click.echo(f"Bridge page successfully generated at: {filepath}")
              except Exception as e:
                  click.echo(f"Error generating bridge page: {e}")
              
          elif choice == 5:
              niche = click.prompt("Enter niche")
              output_video = click.prompt("Enter output video path", default="output.mp4")
              logo_path = click.prompt("Enter logo path (optional)", default="")
              if logo_path == "":
                  logo_path = None
                  
              video_agent = VideoAgent(llm_client)
              click.echo("Generating video script...")
              script_data = video_agent.generate_structured_script(niche)
              scenes = script_data["scenes"]
              
              # Aggregate voiceover text
              voiceover_text = " ".join([s["voiceover_text"] for s in scenes])
              
              audio_path = "temp_voiceover.mp3"
              image_dir = "temp_scenes"
              
              click.echo("Generating voiceover audio...")
              try:
                  word_timestamps = asyncio.run(video_agent.generate_voiceover(voiceover_text, audio_path))
                  click.echo("Generating scene images...")
                  image_paths = video_agent.generate_scene_images(scenes, image_dir)
                  click.echo("Composing video file (this might take a few moments)...")
                  video_agent.compose_video(
                      scenes=scenes,
                      images=image_paths,
                      audio_path=audio_path,
                      word_timestamps=word_timestamps,
                      output_video_path=output_video,
                      logo_path=logo_path
                  )
                  click.echo(f"Video successfully composed at: {output_video}")
              except Exception as e:
                  click.echo(f"Error composing video: {e}")
              finally:
                  # Clean up temp assets if they exist
                  if os.path.exists(audio_path):
                      try:
                          os.remove(audio_path)
                      except Exception:
                          pass
                  if os.path.exists(image_dir):
                      import shutil
                      try:
                          shutil.rmtree(image_dir)
                      except Exception:
                          pass
              
          elif choice == 6:
              niche = click.prompt("Enter niche")
              platform = click.prompt("Enter platform (e.g. Reddit)", default="Reddit")
              thread_title = click.prompt("Enter thread title")
              thread_content = click.prompt("Enter thread content")
              ref_blog_url = click.prompt("Enter reference blog URL")
              
              social_agent = SocialAgent(llm_client)
              thread = {"title": thread_title, "content": thread_content}
              click.echo("Analyzing thread relevance...")
              try:
                  if social_agent.is_relevant(thread, niche):
                      click.echo("Thread is relevant! Generating reply...")
                      reply = social_agent.generate_reply(thread, ref_blog_url)
                      click.echo("\n--- Generated Reply ---")
                      click.echo(reply)
                      click.echo("----------------------")
                  else:
                      click.echo("Thread is NOT relevant to the niche.")
              except Exception as e:
                  click.echo(f"Error managing social lead: {e}")
              
          elif choice == 7:
              click.echo("Exiting wizard. Goodbye!")
              break
  ```

- [ ] **Step 2: Commit the changes**
  Run:
  ```bash
  git add src/my_automated_traffic/cli.py
  git commit -m "feat: implement interactive wizard menu in cli.py"
  ```

---

### Task 2: Verify and Test the Wizard

**Files:**
- None (verification task)

- [ ] **Step 1: Verify the CLI test suite still passes**
  Run: `uv run pytest`
  Expected: All 28 tests pass successfully.

- [ ] **Step 2: Test wizard execution**
  Run the tool with no arguments:
  ```bash
  uv run my-automated-traffic
  ```
  Verify that:
  - The menu displays options 1-7.
  - Option 1 correctly asks for inputs and adds an offer.
  - Option 7 exits cleanly.
