import os
import pytest
from unittest.mock import MagicMock
from src.video_agent import VideoAgent

def test_video_script_draft():
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "Hook: Want to know if she likes you? \nBody: Check if she leans in when talking. \nCTA: Click link in bio to test your score."
    
    agent = VideoAgent(llm_client=mock_llm)
    script = agent.generate_script(niche="dating")
    
    assert "Hook:" in script
    assert "CTA:" in script
    
def test_tts_generation(tmp_path):
    mock_llm = MagicMock()
    agent = VideoAgent(llm_client=mock_llm)
    
    audio_file = os.path.join(tmp_path, "test.mp3")
    agent.generate_audio("Hello World from TTS", audio_file)
    assert os.path.exists(audio_file)
