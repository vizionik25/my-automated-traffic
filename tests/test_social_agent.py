import pytest
from unittest.mock import MagicMock
from my_automated_traffic.social_agent import SocialAgent

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
    
    with pytest.raises(ValueError):
        SocialAgent(llm_client=None)  # type: ignore

    agent = SocialAgent(llm_client=mock_llm)
    
    # Test invalid threads for is_relevant
    with pytest.raises(ValueError):
        agent.is_relevant(None, niche="dating")  # type: ignore
    
    with pytest.raises(ValueError):
        agent.is_relevant({}, niche="dating")
        
    with pytest.raises(ValueError):
        agent.is_relevant({"title": ""}, niche="dating")
        
    with pytest.raises(ValueError):
        agent.is_relevant({"title": "some title", "content": ""}, niche="dating")
        
    # Test invalid niche with valid thread
    with pytest.raises(ValueError):
        agent.is_relevant({"title": "some title", "content": "some content"}, niche="")

    # Test invalid inputs for generate_reply
    with pytest.raises(ValueError):
        agent.generate_reply(None, ref_blog_url="http://blog.com/dating-tips")  # type: ignore
        
    # Test invalid urls with valid thread
    with pytest.raises(ValueError):
        agent.generate_reply({"title": "some title", "content": "some content"}, ref_blog_url="")

    with pytest.raises(ValueError):
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

def test_social_agent_is_relevant_punctuation() -> None:
    """Test that is_relevant strips trailing punctuation from LLM responses."""
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "Yes!."
    agent = SocialAgent(llm_client=mock_llm)
    thread = {"title": "some title", "content": "some content"}
    assert agent.is_relevant(thread, niche="dating") is True
