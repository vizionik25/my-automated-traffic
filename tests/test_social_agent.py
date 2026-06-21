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
    
    with pytest.raises(ValueError):
        SocialAgent(llm_client=None)

    agent = SocialAgent(llm_client=mock_llm)
    
    # Test invalid threads for is_relevant
    with pytest.raises(ValueError):
        agent.is_relevant(None, niche="dating")
    
    with pytest.raises(ValueError):
        agent.is_relevant({}, niche="dating")
        
    with pytest.raises(ValueError):
        agent.is_relevant({"title": ""}, niche="dating")
        
    with pytest.raises(ValueError):
        agent.is_relevant({"title": "some title", "content": ""}, niche="")

    # Test invalid inputs for generate_reply
    with pytest.raises(ValueError):
        agent.generate_reply(None, ref_blog_url="http://blog.com/dating-tips")
        
    with pytest.raises(ValueError):
        agent.generate_reply({"title": "some title"}, ref_blog_url="")

    with pytest.raises(ValueError):
        agent.generate_reply({"title": "some title"}, ref_blog_url="not_a_url")
