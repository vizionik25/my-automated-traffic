import pytest
from unittest.mock import MagicMock
from src.blog_agent import BlogAgent

def test_blog_post_generation():
    mock_llm = MagicMock()
    # Mocking standard generate method
    mock_llm.generate.return_value = "Mocked helpful SFW relationship advice blog post content."
    
    agent = BlogAgent(llm_client=mock_llm)
    post = agent.generate_post(
        keyword="how to start a conversation with a girl",
        niche="dating",
        bridge_url="http://localhost:8000/dating_quiz.html"
    )
    
    assert post["keyword"] == "how to start a conversation with a girl"
    assert "dating" in post["title"].lower() or "conversation" in post["title"].lower()
    assert "Mocked helpful SFW" in post["content"]
    assert "http://localhost:8000/dating_quiz.html" in post["content"]

    mock_llm.generate.assert_called_once_with(
        "Write a SFW dating blog post about: 'how to start a conversation with a girl'. Soft pitch this quiz link at the end: http://localhost:8000/dating_quiz.html."
    )
