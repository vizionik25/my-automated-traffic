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


def test_generate_voiceover(tmp_path):
    import asyncio
    from unittest.mock import AsyncMock

    mock_llm = MagicMock()
    agent = VideoAgent(llm_client=mock_llm)
    
    # We will mock the edge_tts Communicate to prevent network calls
    with patch("my_automated_traffic.video_agent.edge_tts.Communicate") as mock_comm:
        mock_instance = AsyncMock()
        mock_comm.return_value = mock_instance
        
        # Mocking the generator of events/submaker data
        async def mock_iterate():
            # Yield chunks simulating word boundary events
            yield {"type": "audio", "data": b"fake audio chunk"}
            yield {"type": "WordBoundary", "offset": 10000000, "duration": 5000000, "text": "Dating"}
            yield {"type": "WordBoundary", "offset": 15000000, "duration": 5000000, "text": "tips"}
            
        mock_instance.stream = mock_iterate
        
        audio_file = os.path.join(tmp_path, "voiceover.mp3")
        timestamps = asyncio.run(agent.generate_voiceover("Dating tips", audio_file))
        
        assert len(timestamps) == 2
        assert timestamps[0]["word"] == "Dating"
        assert timestamps[0]["start"] == 1.0  # 10M ticks = 1s
        assert timestamps[0]["end"] == 1.5


def test_generate_scene_images(tmp_path):
    mock_llm = MagicMock()
    # We will mock the Imagen client's generate_images response
    mock_imagen = MagicMock()
    mock_image_obj = MagicMock()
    mock_image_obj.bytes = b"fake image bytes"
    mock_imagen.generate_images.return_value = MagicMock(generated_images=[mock_image_obj])
    
    agent = VideoAgent(llm_client=mock_llm, imagen_client=mock_imagen)
    scenes = [
        {"scene_number": 1, "visual_prompt": "Cozy cafe"}
    ]
    
    image_paths = agent.generate_scene_images(scenes, str(tmp_path))
    assert len(image_paths) == 1
    assert os.path.exists(image_paths[0])
    with open(image_paths[0], "rb") as f:
        assert f.read() == b"fake image bytes"
        
def test_generate_scene_images_fallback(tmp_path):
    mock_llm = MagicMock()
    # Imagen client throws an exception
    mock_imagen = MagicMock()
    mock_imagen.generate_images.side_effect = Exception("API error")
    
    agent = VideoAgent(llm_client=mock_llm, imagen_client=mock_imagen)
    scenes = [
        {"scene_number": 1, "visual_prompt": "Cozy cafe"}
    ]
    
    image_paths = agent.generate_scene_images(scenes, str(tmp_path))
    assert len(image_paths) == 1
    assert os.path.exists(image_paths[0])
    # Should create a valid gradient or solid fallback image (check that size is > 0)
    assert os.path.getsize(image_paths[0]) > 0


def test_render_caption_frame(tmp_path):
    mock_llm = MagicMock()
    agent = VideoAgent(llm_client=mock_llm)
    
    frame_path = os.path.join(tmp_path, "caption_frame.png")
    words = ["Decoding", "their", "signs"]
    result_path = agent.render_caption_frame(words, active_index=1, output_path=frame_path)
    
    assert os.path.exists(result_path)
    assert os.path.getsize(result_path) > 0



