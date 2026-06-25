"""Pipeline orchestrator that chains content agents after offer creation.

Runs Bridge Page → Blog Post → Video sequentially, saves outputs to
a structured directory, and generates a markdown deployment report.
"""

import os
import asyncio
import shutil
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import click

from my_automated_traffic.database import DatabaseManager
from my_automated_traffic.blog_agent import BlogAgent
from my_automated_traffic.bridge_page import QuizPageGenerator
from my_automated_traffic.video_agent import VideoAgent


class PipelineOrchestrator:
    """Orchestrates the full content generation pipeline for a campaign.

    After an offer is added, this class:
    1. Creates a campaign in the database
    2. Generates a bridge page (QuizPageGenerator)
    3. Generates a blog post (BlogAgent)
    4. Generates a video asset (VideoAgent)
    5. Produces a markdown report with file locations and deployment instructions
    """

    def __init__(self, llm_client: Any, db: DatabaseManager, base_output_dir: str = "output") -> None:
        """Initialize the orchestrator.

        Args:
            llm_client: An LLM client with a generate(prompt) -> str method.
            db: The database manager instance.
            base_output_dir: Root directory for campaign output folders.
        """
        self.llm_client = llm_client
        self.db = db
        self.base_output_dir = os.path.abspath(base_output_dir)

    def run(self, offer_id: int, campaign_name: str) -> str:
        """Run the full pipeline for an offer.

        Args:
            offer_id: The database ID of the offer.
            campaign_name: Name for the new campaign.

        Returns:
            Absolute path to the generated REPORT.md file.
        """
        # Fetch offer details
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, url, description, compliance_rules, niche FROM offers WHERE id = ?", (offer_id,))
            offer = cursor.fetchone()

        if not offer:
            raise ValueError(f"Offer with ID {offer_id} not found.")

        offer_url = offer["url"]
        niche = offer["niche"]
        description = offer["description"] or ""
        compliance_rules = offer["compliance_rules"] or ""

        # Create campaign
        campaign_id = self.db.add_campaign(offer_id, campaign_name)
        self.db.update_campaign_status(campaign_id, "active")
        click.echo(f"\n✓ Campaign '{campaign_name}' created (ID: {campaign_id})")

        # Setup output directories
        safe_name = campaign_name.lower().replace(" ", "-")
        campaign_dir = os.path.join(self.base_output_dir, safe_name)
        bridge_dir = os.path.join(campaign_dir, "bridge")
        blog_dir = os.path.join(campaign_dir, "blog")
        video_dir = os.path.join(campaign_dir, "video")

        for d in [bridge_dir, blog_dir, video_dir]:
            os.makedirs(d, exist_ok=True)

        click.echo(f"✓ Output directory created: {campaign_dir}")

        # Track results for report
        results: Dict[str, Any] = {
            "campaign_name": campaign_name,
            "campaign_id": campaign_id,
            "offer_id": offer_id,
            "offer_url": offer_url,
            "niche": niche,
            "description": description,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "bridge_page": None,
            "blog_post": None,
            "video": None,
            "errors": [],
        }

        # Step 1: Bridge Page
        click.echo("\n─── Step 1/3: Generating Bridge Page ───")
        try:
            generator = QuizPageGenerator(bridge_dir)
            bridge_title = f"{niche.capitalize()} Compatibility Quiz"
            bridge_path = generator.generate(bridge_title, offer_url, niche)
            results["bridge_page"] = {
                "path": bridge_path,
                "title": bridge_title,
                "filename": os.path.basename(bridge_path),
            }
            click.echo(f"  ✓ Bridge page saved: {bridge_path}")
        except Exception as e:
            error_msg = f"Bridge page generation failed: {e}"
            results["errors"].append(error_msg)
            click.echo(f"  ✗ {error_msg}")

        # Step 2: Blog Post
        click.echo("\n─── Step 2/3: Generating Blog Post ───")
        try:
            agent = BlogAgent(self.llm_client)
            # Use bridge page path as the link reference
            bridge_url = results["bridge_page"]["path"] if results["bridge_page"] else offer_url
            keyword = f"{niche} tips"
            post = agent.generate_post(keyword, niche, bridge_url)

            blog_filename = "blog_post.md"
            blog_path = os.path.join(blog_dir, blog_filename)
            with open(blog_path, "w", encoding="utf-8") as f:
                f.write(post["content"])

            results["blog_post"] = {
                "path": blog_path,
                "title": post["title"],
                "keyword": post["keyword"],
                "filename": blog_filename,
            }
            click.echo(f"  ✓ Blog post saved: {blog_path}")
        except Exception as e:
            error_msg = f"Blog post generation failed: {e}"
            results["errors"].append(error_msg)
            click.echo(f"  ✗ {error_msg}")

        # Step 3: Video
        click.echo("\n─── Step 3/3: Generating Video Asset ───")
        try:
            video_agent = VideoAgent(self.llm_client)
            click.echo("  Generating video script...")
            script_data = video_agent.generate_structured_script(niche)
            scenes = script_data["scenes"]

            voiceover_text = " ".join([s["voiceover_text"] for s in scenes])

            audio_path = os.path.join(video_dir, "voiceover.mp3")
            image_dir = os.path.join(video_dir, "scenes")
            output_video = os.path.join(video_dir, "output.mp4")

            click.echo("  Generating voiceover audio...")
            word_timestamps = asyncio.run(video_agent.generate_voiceover(voiceover_text, audio_path))

            click.echo("  Generating scene images...")
            image_paths = video_agent.generate_scene_images(scenes, image_dir)

            click.echo("  Composing video (this may take a moment)...")
            video_agent.compose_video(
                scenes=scenes,
                images=image_paths,
                audio_path=audio_path,
                word_timestamps=word_timestamps,
                output_video_path=output_video,
            )

            results["video"] = {
                "path": output_video,
                "audio_path": audio_path,
                "scenes_dir": image_dir,
                "filename": "output.mp4",
            }
            click.echo(f"  ✓ Video saved: {output_video}")

            # Clean up intermediate scene images
            if os.path.exists(image_dir):
                shutil.rmtree(image_dir, ignore_errors=True)

        except Exception as e:
            error_msg = f"Video generation failed: {e}"
            results["errors"].append(error_msg)
            click.echo(f"  ✗ {error_msg}")

        # Step 4: Generate Report
        click.echo("\n─── Generating Deployment Report ───")
        report_path = self._generate_report(campaign_dir, results)
        click.echo(f"  ✓ Report saved: {report_path}")

        return report_path

    def _generate_report(self, campaign_dir: str, results: Dict[str, Any]) -> str:
        """Generate a markdown deployment report.

        Args:
            campaign_dir: The campaign output directory.
            results: Dictionary of pipeline results and metadata.

        Returns:
            Absolute path to the generated report file.
        """
        lines = []
        lines.append(f"# Campaign Report: {results['campaign_name']}")
        lines.append("")
        lines.append(f"**Generated:** {results['timestamp']}")
        lines.append(f"**Campaign ID:** {results['campaign_id']}")
        lines.append(f"**Offer ID:** {results['offer_id']}")
        lines.append(f"**Offer URL:** {results['offer_url']}")
        lines.append(f"**Niche:** {results['niche']}")
        if results["description"]:
            lines.append(f"**Description:** {results['description']}")
        lines.append("")

        # Generated Assets
        lines.append("## Generated Assets")
        lines.append("")
        lines.append("| Asset | File | Path |")
        lines.append("|-------|------|------|")

        if results["bridge_page"]:
            bp = results["bridge_page"]
            lines.append(f"| Bridge Page | `{bp['filename']}` | `{bp['path']}` |")
        if results["blog_post"]:
            bl = results["blog_post"]
            lines.append(f"| Blog Post | `{bl['filename']}` | `{bl['path']}` |")
        if results["video"]:
            v = results["video"]
            lines.append(f"| Video | `{v['filename']}` | `{v['path']}` |")
            lines.append(f"| Voiceover Audio | `voiceover.mp3` | `{v['audio_path']}` |")

        lines.append("")

        # Errors
        if results["errors"]:
            lines.append("## ⚠️ Errors")
            lines.append("")
            for err in results["errors"]:
                lines.append(f"- {err}")
            lines.append("")

        # Deployment Instructions
        lines.append("## Deployment Instructions")
        lines.append("")

        if results["bridge_page"]:
            lines.append("### Bridge Page")
            lines.append("")
            lines.append(f"1. Upload `{results['bridge_page']['filename']}` to your web hosting provider")
            lines.append("2. Configure your domain/subdomain to point to the hosted file")
            lines.append("3. Update the bridge page URL in your blog posts and social media links")
            lines.append("4. Test the CTA button redirects correctly to the affiliate offer")
            lines.append("")

        if results["blog_post"]:
            lines.append("### Blog Post")
            lines.append("")
            lines.append(f"1. Open `{results['blog_post']['filename']}` — it's in Markdown format")
            lines.append("2. Copy the content into your CMS (WordPress, Ghost, etc.)")
            lines.append("3. Update the quiz link in the blog post to your deployed bridge page URL")
            lines.append("4. Add relevant images/media before publishing")
            lines.append("5. Publish and submit to search engines (Google Search Console)")
            lines.append("")

        if results["video"]:
            lines.append("### Video")
            lines.append("")
            lines.append(f"1. The video file is at `{results['video']['path']}`")
            lines.append("2. Upload to TikTok, YouTube Shorts, and/or Instagram Reels")
            lines.append("3. Add your bridge page URL as the 'link in bio'")
            lines.append("4. Use niche-relevant hashtags for discoverability")
            lines.append("5. Post during peak engagement hours for your target audience")
            lines.append("")

        # SocialAgent Manual Usage
        lines.append("### Social Media Lead Generation (Manual)")
        lines.append("")
        lines.append("The SocialAgent is not part of the automated pipeline because it requires")
        lines.append("existing social media threads to analyze and respond to. Use it manually:")
        lines.append("")
        lines.append("1. Run the CLI wizard: `my-automated-traffic`")
        lines.append("2. Select option **6. Manage Social Leads (SocialAgent)**")
        lines.append("3. Enter your niche, platform, thread title/content, and blog URL")
        lines.append("4. The agent will analyze relevance and generate a helpful reply")
        lines.append("")
        lines.append("**Tip:** Use your published blog post URL as the reference link for maximum SEO value.")
        lines.append("")

        # Environment Setup Reference
        lines.append("## Environment Setup")
        lines.append("")
        lines.append("This pipeline requires the following environment variables:")
        lines.append("")
        lines.append("```bash")
        lines.append("export OPENAI_API_BASE=https://api.openai.com/v1   # or any OpenAI-compatible endpoint")
        lines.append("export OPENAI_API_KEY=sk-your-key-here")
        lines.append("export OPENAI_MODEL=gpt-4o-mini                    # optional, defaults to gpt-4o-mini")
        lines.append("```")
        lines.append("")
        lines.append("Compatible providers: OpenAI, OpenRouter, Ollama, LM Studio, Azure OpenAI, etc.")
        lines.append("")

        report_content = "\n".join(lines)
        report_path = os.path.join(campaign_dir, "REPORT.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        return report_path
