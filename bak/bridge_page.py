import os
import html
import re

class QuizPageGenerator:
    """Generates SFW pre-lander quiz landing pages to bridge traffic to NSFW affiliate links."""

    def __init__(self, output_dir: str) -> None:
        """Initialize the QuizPageGenerator with a directory to save generated HTML files."""
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

    def render_html(self, title: str, offer_url: str) -> str:
        """Render the HTML content with safe escaping and structure."""
        if not (offer_url.startswith("http://") or offer_url.startswith("https://")):
            raise ValueError("Offer URL must start with http:// or https://")

        escaped_title = html.escape(title)
        escaped_url = html.escape(offer_url)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escaped_title}</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; background-color: #fafafa; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
        .card {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; max-width: 400px; }}
        button {{ background: #4f46e5; color: white; border: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="card">
        <h2>{escaped_title}</h2>
        <p>Complete this simple test to reveal your custom relationship compatibility profile.</p>
        <button id="cta-button" data-url="{escaped_url}">Begin Assessment</button>
    </div>
    <script>
        document.getElementById("cta-button").addEventListener("click", function() {{
            const url = this.getAttribute("data-url");
            const consent = confirm("You are about to be redirected. You must be over 18 to proceed. Do you agree?");
            if (consent) {{
                window.location.href = url;
            }}
        }});
    </script>
</body>
</html>
"""

    def generate(self, title: str, offer_url: str, niche: str) -> str:
        """Generate a static HTML bridge page and return its file path."""
        # Sanitize niche to prevent path traversal
        clean_niche = re.sub(r'[^a-zA-Z0-9_\-]', '', niche)
        if not clean_niche or clean_niche != niche:
            raise ValueError("Invalid niche name specified")

        html_content = self.render_html(title, offer_url)
        filename = f"{clean_niche}_quiz.html"
        filepath = os.path.abspath(os.path.join(self.output_dir, filename))

        # Enforce that the output file path is strictly within the output directory
        if os.path.commonpath([self.output_dir, filepath]) != self.output_dir:
            raise ValueError("Path traversal attempt detected")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return filepath
