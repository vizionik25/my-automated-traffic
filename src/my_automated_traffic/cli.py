"""Command Line Interface (CLI) orchestrator for the Affiliate Strategy suite."""

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

@click.group()
@click.option('--db-path', default='campaigns.db', help='Path to SQLite database')
@click.pass_context
def main_cli(ctx: click.Context, db_path: str) -> None:
    """Main command line entry point for the campaign orchestrator.

    Args:
        ctx: The Click context object.
        db_path: Path to the SQLite campaign database.
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

if __name__ == '__main__':
    main_cli(obj={})
