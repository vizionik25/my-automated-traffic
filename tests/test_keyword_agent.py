import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from my_automated_traffic.keyword_agent import KeywordAgent

@patch('my_automated_traffic.keyword_agent.TrendReq')
def test_discover_keyword_success(mock_trendreq_class):
    # 1. Setup mock data returned by pytrends
    mock_pytrend_instance = MagicMock()
    mock_trendreq_class.return_value = mock_pytrend_instance

    top_df = pd.DataFrame({"query": ["dating tips", "how to talk to girls"], "value": [100, 80]})
    rising_df = pd.DataFrame({"query": ["dating advice free", "online dating hacks"], "value": [150, 120]})
    
    mock_pytrend_instance.related_queries.return_value = {
        "dating": {
            "top": top_df,
            "rising": rising_df
        }
    }

    # 2. Setup mock LLM client
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "online dating hacks"

    # 3. Execute KeywordAgent
    agent = KeywordAgent(llm_client=mock_llm)
    keyword = agent.discover_keyword("dating")

    # 4. Assertions
    assert keyword == "online dating hacks"
    mock_pytrend_instance.build_payload.assert_called_once_with(kw_list=["dating"], timeframe="today 3-m")
    mock_llm.generate.assert_called_once()
    assert "dating tips" in mock_llm.generate.call_args[0][0]
    assert "online dating hacks" in mock_llm.generate.call_args[0][0]


@patch('my_automated_traffic.keyword_agent.TrendReq')
def test_discover_keyword_fallback_on_empty(mock_trendreq_class):
    # 1. Setup mock returned by pytrends (empty dict)
    mock_pytrend_instance = MagicMock()
    mock_trendreq_class.return_value = mock_pytrend_instance
    mock_pytrend_instance.related_queries.return_value = {}

    # 2. Setup mock LLM client (returning brainstormed keyword)
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "dating communication tips"

    # 3. Execute KeywordAgent
    agent = KeywordAgent(llm_client=mock_llm)
    keyword = agent.discover_keyword("dating")

    # 4. Assertions
    assert keyword == "dating communication tips"
    # Fallback prompt is executed
    assert "Brainstorm 10 popular" in mock_llm.generate.call_args[0][0]


@patch('my_automated_traffic.keyword_agent.TrendReq')
def test_discover_keyword_fallback_on_exception(mock_trendreq_class):
    # 1. Setup mock to raise an exception
    mock_pytrend_instance = MagicMock()
    mock_trendreq_class.return_value = mock_pytrend_instance
    mock_pytrend_instance.related_queries.side_effect = Exception("Rate limit block")

    # 2. Setup mock LLM client
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "relationship building blocks"

    # 3. Execute KeywordAgent
    agent = KeywordAgent(llm_client=mock_llm)
    keyword = agent.discover_keyword("dating")

    # 4. Assertions
    assert keyword == "relationship building blocks"
    assert "Brainstorm 10 popular" in mock_llm.generate.call_args[0][0]
