import pytest
from unittest.mock import MagicMock
from src.social_agent import SocialAgent

def test_filter_and_reply() -> None:
    """Test filtering of relevant threads and response generation with the SocialAgent."""
    mock_llm = MagicMock()
    # Mocking two replies: first for is_relevant (should return Yes/No), second for reply_content
    mock_llm.generate.side_effect = ["Yes", "Try starting with a warm smile and asking about her day."]
    
    agent = SocialAgent(llm_client=mock_llm)
    thread = {
        "id": "t1_abc",
        "title": "I am too scared to talk to girls, how do I start a conversation?",
        "content": "Every time I see someone I like, I freeze up. Help!"
    }
    
    is_relevant = agent.is_relevant(thread, niche="dating")
    assert is_relevant is True
    
    reply = agent.generate_reply(thread, ref_blog_url="http://blog.com/dating-tips")
    assert "smile" in reply
    assert "http://blog.com/dating-tips" in reply

def test_social_agent_validation() -> None:
    """Test parameter validations in SocialAgent."""
    mock_llm = MagicMock()
    
    with pytest.raises(ValueError, match="llm_client cannot be None"):
        SocialAgent(llm_client=None)  # type: ignore

    agent = SocialAgent(llm_client=mock_llm)
    
    # Test invalid threads for is_relevant
    with pytest.raises(ValueError, match="thread must be a non-empty dictionary"):
        agent.is_relevant(None, niche="dating")  # type: ignore
    
    with pytest.raises(ValueError, match="thread must be a non-empty dictionary"):
        agent.is_relevant({}, niche="dating")

    with pytest.raises(ValueError, match="thread must contain 'title' and 'content' keys"):
        agent.is_relevant({"id": "t1"}, niche="dating")
        
    with pytest.raises(ValueError, match="thread title must be a non-empty string"):
        agent.is_relevant({"title": "", "content": "some content"}, niche="dating")
        
    with pytest.raises(ValueError, match="thread content must be a non-empty string"):
        agent.is_relevant({"title": "some title", "content": "   "}, niche="dating")

    with pytest.raises(ValueError, match="niche must be a non-empty string"):
        agent.is_relevant({"title": "some title", "content": "some content"}, niche="")

    # Test invalid inputs for generate_reply
    with pytest.raises(ValueError, match="thread must be a non-empty dictionary"):
        agent.generate_reply(None, ref_blog_url="http://blog.com/dating-tips")  # type: ignore
        
    with pytest.raises(ValueError, match="ref_blog_url must be a non-empty string"):
        agent.generate_reply({"title": "some title", "content": "some content"}, ref_blog_url="")

    with pytest.raises(ValueError, match="ref_blog_url must start with http:// or https://"):
        agent.generate_reply({"title": "some title", "content": "some content"}, ref_blog_url="not_a_url")

def test_social_agent_llm_failure() -> None:
    """Test LLM response failure for generate_reply (returns empty/None)."""
    mock_llm = MagicMock()
    agent = SocialAgent(llm_client=mock_llm)
    thread = {"title": "some title", "content": "some content"}

    mock_llm.generate.return_value = None
    with pytest.raises(RuntimeError, match="Failed to generate a valid reply from LLM"):
        agent.generate_reply(thread, ref_blog_url="http://blog.com")

    mock_llm.generate.return_value = ""
    with pytest.raises(RuntimeError, match="Failed to generate a valid reply from LLM"):
        agent.generate_reply(thread, ref_blog_url="http://blog.com")
        
    mock_llm.generate.return_value = "   "
    with pytest.raises(RuntimeError, match="Failed to generate a valid reply from LLM"):
        agent.generate_reply(thread, ref_blog_url="http://blog.com")
