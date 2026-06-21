from typing import Dict

class BlogAgent:
    """Agent responsible for researching keywords and generating SFW SEO blog articles linking to the bridge pre-lander."""

    def __init__(self, llm_client) -> None:
        """Initialize the BlogAgent with an LLM client wrapper."""
        self.llm_client = llm_client

    def generate_post(self, keyword: str, niche: str, bridge_url: str) -> Dict[str, str]:
        """Generate a SFW blog post dictionary containing title, keyword, and content."""
        prompt = f"Write a SFW {niche} blog post about: '{keyword}'. Soft pitch this quiz link at the end: {bridge_url}."
        generated_content = self.llm_client.generate(prompt)
        
        title = f"{niche.capitalize()}: {keyword.capitalize()}"
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
