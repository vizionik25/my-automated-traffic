import os
import click
from typing import List, Any
from pytrends.request import TrendReq

class KeywordAgent:
    """Agent responsible for automated keyword research using Google Trends."""

    def __init__(self, llm_client: Any) -> None:
        """Initialize the KeywordAgent with an LLM client wrapper."""
        self.llm_client = llm_client

    def fetch_trends_queries(self, niche: str) -> List[str]:
        """Fetch related queries (top & rising) from Google Trends.

        Args:
            niche: The search niche (e.g. 'dating').

        Returns:
            A list of search queries returned by Google Trends.
        """
        # Initialize TrendReq with standard headers, timezone, and language
        pytrend = TrendReq(hl='en-US', tz=360, retries=2, backoff_factor=0.5)
        
        # Build payload for the niche
        pytrend.build_payload(kw_list=[niche], timeframe='today 3-m')
        
        related_queries_dict = pytrend.related_queries()
        if not related_queries_dict or niche not in related_queries_dict:
            return []

        niche_data = related_queries_dict[niche]
        queries = []

        # Extract queries from 'top' and 'rising' DataFrames
        for category in ('top', 'rising'):
            df = niche_data.get(category)
            if df is not None and not df.empty:
                # Retrieve the query column as a list of strings
                queries.extend(df['query'].tolist())

        return list(dict.fromkeys(queries))  # Remove duplicates preserving order

    def select_optimal_keyword(self, niche: str, queries: List[str]) -> str:
        """Call the LLM to select the most optimal long-tail keyword from Google Trends.

        Args:
            niche: The search niche.
            queries: The list of raw keywords from Google Trends.

        Returns:
            The selected optimal keyword.
        """
        if not queries:
            raise ValueError("No queries available for selection.")

        queries_str = "\n".join([f"- {q}" for q in queries[:20]])  # Limit to top 20 queries

        prompt = (
            f"Analyze the following list of Google Trends search terms related to the niche '{niche}':\n"
            f"{queries_str}\n\n"
            f"Select the single most optimal SFW keyword for an affiliate marketing blog post.\n"
            f"Requirements:\n"
            f"1. Must have high intent/relevance to the niche: '{niche}'\n"
            f"2. Must be low-competition, specifically favoring long-tail search queries (phrases of 2-5 words) rather than highly competitive generic terms (like '{niche}' itself).\n"
            f"3. Must be safe for work (SFW).\n\n"
            f"Respond ONLY with the selected keyword string (no markdown, no quotes, no explanation, no preamble)."
        )

        selected = self.llm_client.generate(prompt)
        # Clean selected output (strip quotes, spaces, markdown bold, etc.)
        clean_selected = selected.replace("`", "").replace("'", "").replace('"', "").replace("*", "").strip()
        return clean_selected

    def discover_keyword(self, niche: str) -> str:
        """Discover the most optimal SFW long-tail keyword using Google Trends.
        
        If Trends fails or is rate-limited, it falls back to LLM brainstorming.

        Args:
            niche: The target niche.

        Returns:
            The discovered keyword as a string.
        """
        click.echo(f"🔍 Executing automated keyword research for niche: '{niche}'...")
        
        try:
            queries = self.fetch_trends_queries(niche)
            if queries:
                click.echo(f"  ✓ Fetched {len(queries)} related queries from Google Trends.")
                optimal_kw = self.select_optimal_keyword(niche, queries)
                click.echo(f"  ✓ Selected optimal keyword: '{optimal_kw}'")
                return optimal_kw
            else:
                click.echo("  ⚠️ No related queries returned from Google Trends. Falling back to LLM ideation...")
        except Exception as e:
            click.echo(f"  ⚠️ Google Trends request failed: {e}. Falling back to LLM ideation...")

        # Fallback: Let LLM brainstorm SFW keywords and choose the best one
        prompt = (
            f"Brainstorm 10 popular, SFW, long-tail search keywords related to the niche '{niche}'.\n"
            f"From those, select the single best keyword that has low competition but high affiliate interest.\n\n"
            f"Respond ONLY with the selected keyword string (no quotes, no explanation, no markdown)."
        )
        optimal_kw = self.llm_client.generate(prompt)
        clean_selected = optimal_kw.replace("`", "").replace("'", "").replace('"', "").replace("*", "").strip()
        click.echo(f"  ✓ Brainstormed optimal keyword: '{clean_selected}'")
        return clean_selected
