"""Command Line Interface (CLI) orchestrator for the Affiliate Strategy suite."""

import click
import os
import asyncio
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

from my_automated_traffic.database import DatabaseManager
from my_automated_traffic.llm_client import OpenAIClient
from my_automated_traffic.blog_agent import BlogAgent
from my_automated_traffic.bridge_page import QuizPageGenerator
from my_automated_traffic.social_agent import SocialAgent
from my_automated_traffic.video_agent import VideoAgent
from my_automated_traffic.orchestrator import PipelineOrchestrator
from my_automated_traffic.keyword_agent import KeywordAgent


def _get_llm_client() -> OpenAIClient:
    """Create and return an OpenAIClient instance.

    Raises:
        EnvironmentError: If required env vars are not set.
    """
    return OpenAIClient()


def run_interactive_wizard(ctx: click.Context) -> None:
    """Runs the main interactive wizard menu."""
    db: DatabaseManager = ctx.obj['db']

    while True:
        click.echo("\n==========================================")
        click.echo("       AFFILIATE STRATEGY WIZARD")
        click.echo("==========================================")
        click.echo("1. Add a New Affiliate Offer (+ Run Automation)")
        click.echo("2. Generate Blog Post (BlogAgent)")
        click.echo("3. Generate Bridge Page (QuizPageGenerator)")
        click.echo("4. Generate Video Asset (VideoAgent)")
        click.echo("5. Manage Social Leads (SocialAgent)")
        click.echo("6. Run Keyword Research (KeywordAgent)")
        click.echo("7. Exit")
        click.echo("==========================================")
        
        choice = click.prompt("Select an option (1-7)", type=int, default=7)
        
        if choice == 1:
            # Collect offer details
            url = click.prompt("Enter offer URL")
            if not (url.startswith("http://") or url.startswith("https://")):
                click.echo("Error: URL must start with http:// or https://")
                continue
            desc = click.prompt("Enter description", default="")
            rules = click.prompt("Enter compliance rules", default="")
            niche = click.prompt("Enter niche")
            offer_id = db.add_offer(url, desc, rules, niche)
            click.echo(f"Successfully added offer with ID: {offer_id}")

            # Prompt for campaign name and run full pipeline
            campaign_name = click.prompt("Enter campaign name")
            click.echo("\n🚀 Starting automation pipeline...")
            try:
                llm_client = _get_llm_client()
                orchestrator = PipelineOrchestrator(llm_client, db)
                report_path = orchestrator.run(offer_id, campaign_name)
                click.echo(f"\n{'='*50}")
                click.echo("✅ Pipeline complete!")
                click.echo(f"📄 Deployment report: {report_path}")
                click.echo(f"{'='*50}")
            except Exception as e:
                click.echo(f"\n❌ Pipeline or Configuration error: {e}")

        elif choice == 2:
            try:
                llm_client = _get_llm_client()
            except Exception as e:
                click.echo(f"\n❌ Configuration error:\n{e}")
                continue
            niche = click.prompt("Enter niche")
            bridge_url = click.prompt("Enter bridge URL")
            kw_agent = KeywordAgent(llm_client)
            keyword = kw_agent.discover_keyword(niche)
            agent = BlogAgent(llm_client)
            post = agent.generate_post(keyword, niche, bridge_url)
            click.echo("\n--- Generated Blog Post ---")
            click.echo(f"Title: {post['title']}")
            click.echo(f"Content:\n{post['content']}")
            click.echo("---------------------------")
            
        elif choice == 3:
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
            
        elif choice == 4:
            try:
                llm_client = _get_llm_client()
            except Exception as e:
                click.echo(f"\n❌ Configuration error:\n{e}")
                continue
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
            
        elif choice == 5:
            try:
                llm_client = _get_llm_client()
            except Exception as e:
                click.echo(f"\n❌ Configuration error:\n{e}")
                continue
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
            
        elif choice == 6:
            try:
                llm_client = _get_llm_client()
            except Exception as e:
                click.echo(f"\n❌ Configuration error:\n{e}")
                continue
            niche = click.prompt("Enter niche")
            kw_agent = KeywordAgent(llm_client)
            try:
                keyword = kw_agent.discover_keyword(niche)
                click.echo(f"\n✅ Discovered Keyword: {keyword}")
            except Exception as e:
                click.echo(f"Error during keyword research: {e}")

        elif choice == 7:
            click.echo("Exiting wizard. Goodbye!")
            break

@click.group(invoke_without_command=True)
@click.option('--db-path', default='campaigns.db', help='Path to SQLite database')
@click.pass_context
def main_cli(ctx: click.Context, db_path: str) -> None:
    """Affiliate Strategy campaign orchestrator.

    Run without a subcommand to launch the interactive wizard.

    \b
    Available commands:
      add-offer      Add a new affiliate offer to the database
      social-reply   Analyze a social media thread and generate a reply

    \b
    Required environment variables:
      OPENAI_API_BASE   API endpoint URL (e.g. https://api.openai.com/v1)
      OPENAI_API_KEY    Your API key
      OPENAI_MODEL      Model identifier (optional, defaults to gpt-4o-mini)
    """
    ctx.ensure_object(dict)
    ctx.obj['db'] = DatabaseManager(db_path)
    ctx.obj['db'].initialize()
    
    if ctx.invoked_subcommand is None:
        run_interactive_wizard(ctx)

@main_cli.command()
@click.option('--url', required=True, help='URL of the affiliate offer')
@click.option('--desc', default='', help='Description of the affiliate offer')
@click.option('--rules', default='', help='Compliance/promotional rules')
@click.option('--niche', required=True, help='Target niche for the offer')
@click.pass_context
def add_offer(ctx: click.Context, url: str, desc: str, rules: str, niche: str) -> None:
    """Add a new affiliate offer to the database.

    Args:
        ctx: The Click context object.
        url: The affiliate offer URL.
        desc: Description of the offer.
        rules: Compliance guidelines or rules.
        niche: Niche for the offer.
    """
    db: DatabaseManager = ctx.obj['db']
    offer_id = db.add_offer(url, desc, rules, niche)
    click.echo(f"Successfully added offer with ID: {offer_id}")

@main_cli.command()
@click.option('--niche', required=True, help='Target niche to check thread relevance against')
@click.option('--thread-title', required=True, help='Title of the social media thread')
@click.option('--thread-content', required=True, help='Body content of the social media thread')
@click.option('--blog-url', required=True, help='Reference blog URL to include in the reply')
@click.option('--platform', default='Reddit', help='Social media platform (default: Reddit)')
@click.pass_context
def social_reply(ctx: click.Context, niche: str, thread_title: str, thread_content: str, blog_url: str, platform: str) -> None:
    """Analyze a social media thread for niche relevance and generate a reply.

    Checks if the thread is relevant to the given niche, then generates a
    helpful, empathetic reply that softly references your blog URL.

    \b
    Example:
      my-automated-traffic social-reply \\
        --niche "dating" \\
        --thread-title "How to approach someone at a coffee shop?" \\
        --thread-content "I keep seeing this person at my local cafe..." \\
        --blog-url "https://myblog.com/dating-tips"
    """
    try:
        llm_client = _get_llm_client()
    except Exception as e:
        click.echo(f"\n❌ Configuration error:\n{e}")
        raise SystemExit(1)

    social_agent = SocialAgent(llm_client)
    thread = {"title": thread_title, "content": thread_content}

    click.echo(f"Platform: {platform}")
    click.echo(f"Niche: {niche}")
    click.echo("Analyzing thread relevance...")

    try:
        if social_agent.is_relevant(thread, niche):
            click.echo("✓ Thread is relevant! Generating reply...\n")
            reply = social_agent.generate_reply(thread, blog_url)
            click.echo("--- Generated Reply ---")
            click.echo(reply)
            click.echo("-----------------------")
        else:
            click.echo("✗ Thread is NOT relevant to the niche.")
    except Exception as e:
        click.echo(f"Error: {e}")
        raise SystemExit(1)

if __name__ == '__main__':
    main_cli(obj={})
