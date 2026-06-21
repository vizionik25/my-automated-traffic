import os
from unittest.mock import MagicMock, patch
import pytest
from my_automated_traffic.video_agent import VideoAgent

def test_video_script_draft():
    mock_llm = MagicMock()
    mock_llm.generate.return_value = (
        "Hook: Want to know if she likes you? \n"
        "Body: Check if she leans in when talking. \n"
        "CTA: Click link in bio to test your score."
    )
    
    agent = VideoAgent(llm_client=mock_llm)
    script = agent.generate_script(niche="dating")
    
    assert "Hook:" in script
    assert "CTA:" in script

@patch("my_automated_traffic.video_agent.gTTS")
def test_tts_generation(mock_gtts, tmp_path):
    # Mock the gTTS instance and save method
    mock_instance = MagicMock()
    mock_gtts.return_value = mock_instance
    
    # Simulate saving by writing dummy content to disk to verify file existence logic safely
    mock_instance.save.side_effect = lambda path: open(path, "wb").write(b"dummy audio data")
    
    mock_llm = MagicMock()
    agent = VideoAgent(llm_client=mock_llm)
    
    audio_file = os.path.join(tmp_path, "test.mp3")
    result_path = agent.generate_audio("Hello World from TTS", audio_file)
    
    # Assertions
    mock_gtts.assert_called_once_with(text="Hello World from TTS", lang="en")
    mock_instance.save.assert_called_once_with(audio_file)
    assert result_path == audio_file
    assert os.path.exists(audio_file)

def test_tts_generation_empty_text():
    mock_llm = MagicMock()
    agent = VideoAgent(llm_client=mock_llm)
    with pytest.raises(ValueError, match="Text content cannot be empty."):
        agent.generate_audio("", "test.mp3")

def test_tts_generation_empty_path():
    mock_llm = MagicMock()
    agent = VideoAgent(llm_client=mock_llm)
    with pytest.raises(ValueError, match="Output path cannot be empty."):
        agent.generate_audio("Hello", "")

@patch("my_automated_traffic.video_agent.gTTS")
def test_tts_generation_runtime_error(mock_gtts):
    mock_instance = MagicMock()
    mock_gtts.return_value = mock_instance
    mock_instance.save.side_effect = Exception("Disk full")
    
    mock_llm = MagicMock()
    agent = VideoAgent(llm_client=mock_llm)
    with pytest.raises(RuntimeError, match="Failed to generate or save TTS audio: Disk full"):
        agent.generate_audio("Hello", "test.mp3")


def test_generate_structured_script():
    mock_llm = MagicMock()
    mock_llm.generate.return_value = (
        '{"scenes": ['
        '{"scene_number": 1, "voiceover_text": "Hook text", "visual_prompt": "Prompt 1"},'
        '{"scene_number": 2, "voiceover_text": "Body text", "visual_prompt": "Prompt 2"}'
        ']}'
    )
    agent = VideoAgent(llm_client=mock_llm)
    script_data = agent.generate_structured_script(niche="dating")
    
    assert "scenes" in script_data
    assert len(script_data["scenes"]) == 2
    assert script_data["scenes"][0]["voiceover_text"] == "Hook text"
    assert script_data["scenes"][0]["visual_prompt"] == "Prompt 1"
