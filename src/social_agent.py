from typing import Dict, Any, Protocol

class LLMClient(Protocol):
    """Protocol defining the expected interface for an LLM client."""
    def generate(self, prompt: str) -> str:
        """Generate a response text based on the provided prompt."""
        ...

class SocialAgent:
    """Agent responsible for monitoring social media threads, filtering by relevancy, and drafting responses."""

    RELEVANCY_PROMPT_TEMPLATE = (
        "Does the following thread discuss advice queries relating to '{niche}'? "
        "Respond only with Yes or No.\n\n"
        "Title: {title}\n"
        "Content: {content}"
    )

    REPLY_PROMPT_TEMPLATE = (
        "Write a helpful, empathetic SFW response to this thread: '{title}'. "
        "Do not spam. Softly reference this resource link: {ref_blog_url}."
    )

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize the SocialAgent with an LLM client wrapper.

        Args:
            llm_client: The LLM client to perform prompt completions.

        Raises:
            ValueError: If llm_client is None.
        """
        if llm_client is None:
            raise ValueError("llm_client cannot be None")
        self.llm_client = llm_client

    def _validate_thread(self, thread: Dict[str, Any]) -> None:
        """Validate that the thread dictionary is non-empty and contains required fields.

        Args:
            thread: A dictionary representing the thread.

        Raises:
            ValueError: If thread is invalid or lacks required fields.
        """
        if not thread or not isinstance(thread, dict):
            raise ValueError("thread must be a non-empty dictionary")
        if "title" not in thread or "content" not in thread:
            raise ValueError("thread must contain 'title' and 'content' keys")
        if not isinstance(thread["title"], str) or not thread["title"].strip():
            raise ValueError("thread title must be a non-empty string")
        if not isinstance(thread["content"], str) or not thread["content"].strip():
            raise ValueError("thread content must be a non-empty string")

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
        self._validate_thread(thread)
        if not niche or not isinstance(niche, str) or not niche.strip():
            raise ValueError("niche must be a non-empty string")

        prompt = self.RELEVANCY_PROMPT_TEMPLATE.format(
            niche=niche,
            title=thread["title"],
            content=thread["content"]
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
            RuntimeError: If LLM generation fails or returns invalid output.
        """
        self._validate_thread(thread)
        if not ref_blog_url or not isinstance(ref_blog_url, str):
            raise ValueError("ref_blog_url must be a non-empty string")
        if not (ref_blog_url.startswith("http://") or ref_blog_url.startswith("https://")):
            raise ValueError("ref_blog_url must start with http:// or https://")

        prompt = self.REPLY_PROMPT_TEMPLATE.format(
            title=thread["title"],
            ref_blog_url=ref_blog_url
        )
        advice = self.llm_client.generate(prompt)
        if not advice or not isinstance(advice, str) or not advice.strip():
            raise RuntimeError("Failed to generate a valid reply from LLM")
            
        return f"{advice.strip()}\n\nFor more detail, check out: {ref_blog_url}"
