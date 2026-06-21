from typing import Dict, Any

class SocialAgent:
    """Agent responsible for monitoring social media threads, filtering by relevancy, and drafting responses."""

    def __init__(self, llm_client: Any) -> None:
        """Initialize the SocialAgent with an LLM client wrapper.

        Args:
            llm_client: The LLM client to perform prompt completions.

        Raises:
            ValueError: If llm_client is None.
        """
        if llm_client is None:
            raise ValueError("llm_client cannot be None")
        self.llm_client = llm_client

    def is_relevant(self, thread: Dict[str, Any], niche: str) -> bool:
        """Determine if a social thread is relevant to a specific niche using the LLM.

        Args:
            thread: A dictionary representing the thread (must contain 'title' and 'content').
            niche: The niche keyword to check relevance against.

        Returns:
            True if the thread is relevant to the niche, False otherwise.

        Raises:
            ValueError: If the thread format is invalid or niche is empty.
        """
        if not thread or not isinstance(thread, dict):
            raise ValueError("thread must be a non-empty dictionary")
        if "title" not in thread or "content" not in thread:
            raise ValueError("thread must contain 'title' and 'content' keys")
        if not isinstance(thread["title"], str) or not thread["title"].strip():
            raise ValueError("thread title must be a non-empty string")
        if not isinstance(thread["content"], str) or not thread["content"].strip():
            raise ValueError("thread content must be a non-empty string")
        if not niche or not isinstance(niche, str) or not niche.strip():
            raise ValueError("niche must be a non-empty string")

        prompt = (
            f"Does the following thread discuss advice queries relating to '{niche}'? "
            f"Respond only with Yes or No.\n\n"
            f"Title: {thread['title']}\n"
            f"Content: {thread['content']}"
        )
        response = self.llm_client.generate(prompt)
        if not response or not isinstance(response, str):
            return False
        return response.strip().lower() == "yes"

    def generate_reply(self, thread: Dict[str, Any], ref_blog_url: str) -> str:
        """Generate a helpful, empathetic, SFW response referencing a blog URL.

        Args:
            thread: A dictionary representing the thread (must contain 'title' and 'content').
            ref_blog_url: The reference blog post URL to include in the reply.

        Returns:
            The drafted response as a string.

        Raises:
            ValueError: If the thread format is invalid or if ref_blog_url is not a valid URL.
        """
        if not thread or not isinstance(thread, dict):
            raise ValueError("thread must be a non-empty dictionary")
        if "title" not in thread or "content" not in thread:
            raise ValueError("thread must contain 'title' and 'content' keys")
        if not isinstance(thread["title"], str) or not thread["title"].strip():
            raise ValueError("thread title must be a non-empty string")
        if not isinstance(thread["content"], str) or not thread["content"].strip():
            raise ValueError("thread content must be a non-empty string")
        if not ref_blog_url or not isinstance(ref_blog_url, str):
            raise ValueError("ref_blog_url must be a non-empty string")
        if not (ref_blog_url.startswith("http://") or ref_blog_url.startswith("https://")):
            raise ValueError("ref_blog_url must start with http:// or https://")

        prompt = (
            f"Write a helpful, empathetic SFW response to this thread: '{thread['title']}'. "
            f"Do not spam. Softly reference this resource link: {ref_blog_url}."
        )
        advice = self.llm_client.generate(prompt)
        return f"{advice}\n\nFor more detail, check out: {ref_blog_url}"
