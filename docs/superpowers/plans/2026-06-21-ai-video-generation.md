# AI Video Generation Agent (VideoAgent) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a fully automated vertical 9:16 short-form video generator inside `VideoAgent` that creates original videos by calling Google Imagen for scene visuals, edge-tts for voiceover with word-level timings, Pillow for transparent captions, and MoviePy for final video compilation with brand logos and CTA deliverables.

**Architecture:** The agent will fetch a structured script JSON via Gemini, synthesize TTS audio with word timings, generate/fallback vertical scene images, overlay subtitles/branding images, and render/export a final `.mp4` file.

**Tech Stack:** Python 3.14+, uv, Pytest, MoviePy, edge-tts, Pillow, Google GenAI SDK (Imagen)

---

### Task 1: Fix broken imports due to package relocation

**Files:**
- Modify: `src/my_automated_traffic/cli.py`
- Modify: `tests/test_blog_agent.py`
- Modify: `tests/test_bridge_page.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_database.py`
- Modify: `tests/test_social_agent.py`
- Modify: `tests/test_video_agent.py`

- [ ] **Step 1: Update imports in source and test files**

Modify the imports to use `my_automated_traffic` instead of `src` directly.

Update `src/my_automated_traffic/cli.py`:
```python
from my_automated_traffic.database import DatabaseManager
```

Update `tests/test_blog_agent.py`:
```python
from my_automated_traffic.blog_agent import BlogAgent
```

Update `tests/test_bridge_page.py`:
```python
from my_automated_traffic.bridge_page import QuizPageGenerator
```

Update `tests/test_cli.py`:
```python
from my_automated_traffic.cli import main_cli
```

Update `tests/test_database.py`:
```python
from my_automated_traffic.database import DatabaseManager
```

Update `tests/test_social_agent.py`:
```python
from my_automated_traffic.social_agent import SocialAgent
```

Update `tests/test_video_agent.py`:
```python
from my_automated_traffic.video_agent import VideoAgent
```

- [ ] **Step 2: Run pytest to verify imports are fixed**

Run: `uv run pytest`
Expected: Tests should collect successfully and run, though some might fail due to gTTS/other mocks or because packages need to be installed.

- [ ] **Step 3: Commit**

```bash
git add src/my_automated_traffic/cli.py tests/*.py
git commit -m "fix: correct package imports to use my_automated_traffic"
```

---

### Task 2: Install Video Generation Dependencies

- [ ] **Step 1: Install edge-tts, moviepy, and pillow**

Run: `uv add edge-tts moviepy pillow`
Expected: Output showing successful addition of the three packages to `pyproject.toml` and lockfile.

- [ ] **Step 2: Verify installation**

Run: `uv run python -c "import edge_tts, moviepy, PIL; print('Success')"`
Expected: Success

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build: add edge-tts, moviepy, and pillow to dependencies"
```

---

### Task 3: Implement Structured Script Generation

**Files:**
- Modify: `src/my_automated_traffic/video_agent.py`
- Test: `tests/test_video_agent.py`

- [ ] **Step 1: Write the failing test**

Add `test_generate_structured_script` to `tests/test_video_agent.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_video_agent.py::test_generate_structured_script`
Expected: FAIL with AttributeError (no method `generate_structured_script`)

- [ ] **Step 3: Write minimal implementation**

Add the method to `VideoAgent` in `src/my_automated_traffic/video_agent.py`:
```python
    import json
    from typing import Dict, Any

    def generate_structured_script(self, niche: str) -> Dict[str, Any]:
        prompt = (
            f"Write a short SFW relationship advice script about {niche}. "
            "Return JSON only matching this schema:\n"
            "{\n"
            "  \"scenes\": [\n"
            "    {\"scene_number\": 1, \"voiceover_text\": \"text\", \"visual_prompt\": \"visual description\"}\n"
            "  ]\n"
            "}"
        )
        response_text = self.llm_client.generate(prompt)
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Simple fallback parser if LLM wrapped in markdown blocks
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_video_agent.py::test_generate_structured_script`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/my_automated_traffic/video_agent.py tests/test_video_agent.py
git commit -m "feat: implement structured script generation in VideoAgent"
```

---

### Task 4: Implement Voiceover and Word-Level Timestamps

**Files:**
- Modify: `src/my_automated_traffic/video_agent.py`
- Test: `tests/test_video_agent.py`

- [ ] **Step 1: Write the failing test**

Add `test_generate_voiceover` to `tests/test_video_agent.py`:
```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_generate_voiceover(tmp_path):
    mock_llm = MagicMock()
    agent = VideoAgent(llm_client=mock_llm)
    
    # We will mock the edge_tts Communicate to prevent network calls
    with patch("my_automated_traffic.video_agent.edge_tts.Communicate") as mock_comm:
        mock_instance = AsyncMock()
        mock_comm.return_value = mock_instance
        
        # Mocking the generator of events/submaker data
        async def mock_iterate():
            # Yield chunks simulating word boundary events
            yield {"type": "WordBoundary", "offset": 10000000, "duration": 5000000, "text": "Dating"}
            yield {"type": "WordBoundary", "offset": 15000000, "duration": 5000000, "text": "tips"}
            
        mock_instance.stream = mock_iterate
        
        audio_file = os.path.join(tmp_path, "voiceover.mp3")
        timestamps = await agent.generate_voiceover("Dating tips", audio_file)
        
        assert len(timestamps) == 2
        assert timestamps[0]["word"] == "Dating"
        assert timestamps[0]["start"] == 1.0  # 10M ticks = 1s
        assert timestamps[0]["end"] == 1.5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_video_agent.py::test_generate_voiceover`
Expected: FAIL with AttributeError (no method `generate_voiceover`)

- [ ] **Step 3: Write minimal implementation**

Modify `src/my_automated_traffic/video_agent.py` to add `generate_voiceover`:
```python
    import edge_tts
    from typing import List

    async def generate_voiceover(self, text: str, output_audio_path: str) -> List[Dict[str, Any]]:
        if not text:
            raise ValueError("Text content cannot be empty.")
        if not output_audio_path:
            raise ValueError("Output path cannot be empty.")
            
        os.makedirs(os.path.dirname(os.path.abspath(output_audio_path)), exist_ok=True)
        
        communicate = edge_tts.Communicate(text, "en-US-GuyNeural")
        submaker = edge_tts.SubMaker()
        
        # Capture the file stream and generate timestamps
        with open(output_audio_path, "wb") as fp:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    fp.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    submaker.feed(chunk)
                    
        timestamps = []
        for start, end, word in submaker.cue_info():
            # edge-tts SubMaker returns start/end as datetime-like timedelta/seconds
            timestamps.append({
                "word": word,
                "start": start.total_seconds(),
                "end": end.total_seconds()
            })
        return timestamps
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_video_agent.py::test_generate_voiceover`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/my_automated_traffic/video_agent.py tests/test_video_agent.py
git commit -m "feat: implement edge-tts synthesis with word-level timestamps"
```

---

### Task 5: Implement Image Generation with Imagen & Fallback

**Files:**
- Modify: `src/my_automated_traffic/video_agent.py`
- Test: `tests/test_video_agent.py`

- [ ] **Step 1: Write the failing test**

Add `test_generate_scene_images` to `tests/test_video_agent.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_video_agent.py::test_generate_scene_images`
Expected: FAIL with AttributeError

- [ ] **Step 3: Write minimal implementation**

Add `generate_scene_images` and gradient drawing utility inside `VideoAgent`:
```python
    from PIL import Image, ImageDraw

    def _create_fallback_image(self, output_path: str, width: int = 1080, height: int = 1920) -> str:
        # Create a vertical SFW gradient fallback image
        image = Image.new("RGB", (width, height), "#1e1b4b")  # Dark Indigo
        draw = ImageDraw.Draw(image)
        # Draw a simple accent gradient/circle
        draw.ellipse([width//4, height//4, 3*width//4, 3*height//4], fill="#312e81")
        image.save(output_path, "PNG")
        return output_path

    def generate_scene_images(self, scenes: List[Dict[str, Any]], output_dir: str) -> List[str]:
        os.makedirs(output_dir, exist_ok=True)
        image_paths = []
        
        for scene in scenes:
            scene_num = scene["scene_number"]
            prompt = scene["visual_prompt"]
            img_path = os.path.join(output_dir, f"scene_{scene_num}.png")
            
            if not self.imagen_client:
                self._create_fallback_image(img_path)
                image_paths.append(img_path)
                continue
                
            try:
                # Expecting Google GenAI SDK client format:
                # imagen_client.generate_images(prompt=prompt, number_of_images=1, aspect_ratio="9:16")
                result = self.imagen_client.generate_images(
                    prompt=f"{prompt}, high quality, cinematic lighting, safe for work, SFW",
                    number_of_images=1,
                    aspect_ratio="9:16"
                )
                image_bytes = result.generated_images[0].bytes
                with open(img_path, "wb") as f:
                    f.write(image_bytes)
            except Exception as e:
                # Log or print error, fallback to Pillow gradient
                self._create_fallback_image(img_path)
                
            image_paths.append(img_path)
        return image_paths
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_video_agent.py::test_generate_scene_images`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/my_automated_traffic/video_agent.py tests/test_video_agent.py
git commit -m "feat: implement AI image generation with Pillow fallback"
```

---

### Task 6: Implement Pillow Subtitle Renderer

**Files:**
- Modify: `src/my_automated_traffic/video_agent.py`
- Test: `tests/test_video_agent.py`

- [ ] **Step 1: Write the failing test**

Add `test_render_caption_frame` to `tests/test_video_agent.py`:
```python
def test_render_caption_frame(tmp_path):
    mock_llm = MagicMock()
    agent = VideoAgent(llm_client=mock_llm)
    
    frame_path = os.path.join(tmp_path, "caption_frame.png")
    words = ["Decoding", "their", "signs"]
    result_path = agent.render_caption_frame(words, active_index=1, output_path=frame_path)
    
    assert os.path.exists(result_path)
    assert os.path.getsize(result_path) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_video_agent.py::test_render_caption_frame`
Expected: FAIL with AttributeError

- [ ] **Step 3: Write minimal implementation**

Add `render_caption_frame` method to `VideoAgent`:
```python
    from PIL import ImageFont

    def render_caption_frame(
        self,
        words: List[str],
        active_index: int,
        output_path: str,
        width: int = 1080,
        height: int = 1920
    ) -> str:
        # Create a transparent base image
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Load a default font
        try:
            font = ImageFont.load_default(size=48)
        except TypeError:
            font = ImageFont.load_default()
            
        # Draw words centered horizontally, active word highlighted
        text_y = height // 2
        total_width = 0
        word_spacings = []
        
        for w in words:
            # Estimate text width (using default font bounding boxes)
            try:
                w_w = draw.textlength(w + " ", font=font)
            except AttributeError:
                w_w = len(w + " ") * 24  # rough fallback
            word_spacings.append(w_w)
            total_width += w_w
            
        start_x = (width - total_width) // 2
        current_x = start_x
        
        for i, word in enumerate(words):
            color = (255, 255, 0, 255) if i == active_index else (255, 255, 255, 255)
            draw.text((current_x, text_y), word, fill=color, font=font)
            current_x += word_spacings[i]
            
        img.save(output_path, "PNG")
        return output_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_video_agent.py::test_render_caption_frame`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/my_automated_traffic/video_agent.py tests/test_video_agent.py
git commit -m "feat: implement ImageMagick-free Pillow subtitle renderer"
```

---

### Task 7: Implement Video Composition using MoviePy

**Files:**
- Modify: `src/my_automated_traffic/video_agent.py`
- Test: `tests/test_video_agent.py`

- [ ] **Step 1: Write the failing test**

Add `test_compose_video` to `tests/test_video_agent.py`:
```python
def test_compose_video(tmp_path):
    mock_llm = MagicMock()
    agent = VideoAgent(llm_client=mock_llm)
    
    # Create mock inputs (dummy image, dummy MP3)
    dummy_img = os.path.join(tmp_path, "dummy_scene.png")
    Image.new("RGB", (108, 192), "#1e1b4b").save(dummy_img)
    
    dummy_audio = os.path.join(tmp_path, "dummy_audio.mp3")
    with open(dummy_audio, "wb") as f:
        # Minimum valid MP3 frame or dummy bytes
        f.write(b"ID3\x03\x00\x00\x00\x00\x00\x00" + b"\x00" * 100)
        
    scenes = [
        {"scene_number": 1, "voiceover_text": "Dating tips"}
    ]
    word_timestamps = [
        {"word": "Dating", "start": 0.0, "end": 0.5},
        {"word": "tips", "start": 0.5, "end": 1.0}
    ]
    
    output_video = os.path.join(tmp_path, "output.mp4")
    
    # Mock moviepy execution to check pipeline without executing heavy FFmpeg rendering in tests
    with patch("my_automated_traffic.video_agent.ImageClip") as mock_img_clip, \
         patch("my_automated_traffic.video_agent.AudioFileClip") as mock_audio_clip, \
         patch("my_automated_traffic.video_agent.CompositeVideoClip") as mock_composite:
         
         mock_clip_instance = MagicMock()
         mock_img_clip.return_value = mock_clip_instance
         mock_clip_instance.set_duration.return_value = mock_clip_instance
         mock_clip_instance.resize.return_value = mock_clip_instance
         
         # Mock composite to return a clip that responds to write_videofile
         mock_comp_instance = MagicMock()
         mock_composite.return_value = mock_comp_instance
         
         result = agent.compose_video(
             scenes=scenes,
             images=[dummy_img],
             audio_path=dummy_audio,
             word_timestamps=word_timestamps,
             output_video_path=output_video
         )
         
         assert result == output_video
         mock_comp_instance.write_videofile.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_video_agent.py::test_compose_video`
Expected: FAIL with AttributeError

- [ ] **Step 3: Write minimal implementation**

Add `compose_video` to `VideoAgent` in `src/my_automated_traffic/video_agent.py`:
```python
    from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
    import tempfile

    def compose_video(
        self,
        scenes: List[Dict[str, Any]],
        images: List[str],
        audio_path: str,
        word_timestamps: List[Dict[str, Any]],
        output_video_path: str,
        logo_path: str = None,
        deliverable_path: str = None
    ) -> str:
        # Determine total duration from audio
        audio_clip = AudioFileClip(audio_path)
        total_duration = audio_clip.duration
        
        # Calculate duration per scene
        scene_duration = total_duration / len(scenes)
        
        clips = []
        temp_dir = tempfile.mkdtemp()
        
        # 1. Compile background images with gentle zoom animation
        for i, img_path in enumerate(images):
            # Ken Burns effect (10% scale up)
            clip = ImageClip(img_path).set_duration(scene_duration).set_start(i * scene_duration)
            # Gentle resizing function over time
            clip = clip.resize(lambda t: 1.0 + 0.1 * (t / scene_duration))
            clips.append(clip)
            
        # 2. Overlay Logo if provided
        if logo_path and os.path.exists(logo_path):
            logo_clip = ImageClip(logo_path).set_duration(total_duration).resize(width=150)
            # Position top-right
            logo_clip = logo_clip.set_position(("right", "top")).margin(right=30, top=30, opacity=0)
            clips.append(logo_clip)
            
        # 3. Overlay Deliverable mockups during the CTA (last scene)
        if deliverable_path and os.path.exists(deliverable_path):
            cta_start = (len(scenes) - 1) * scene_duration
            cta_duration = scene_duration
            deliverable_clip = (
                ImageClip(deliverable_path)
                .set_start(cta_start)
                .set_duration(cta_duration)
                .resize(width=400)
                .set_position("center")
            )
            clips.append(deliverable_clip)
            
        # 4. Burn subtitles word-by-word
        # Group words by sentence or window of 3 words
        window_size = 3
        words_list = [w["word"] for w in word_timestamps]
        
        for idx, item in enumerate(word_timestamps):
            start_t = item["start"]
            end_t = item["end"]
            
            # Determine window slice
            window_start_idx = max(0, idx - 1)
            window_end_idx = min(len(word_timestamps), window_start_idx + window_size)
            window_words = words_list[window_start_idx:window_end_idx]
            active_pos_in_window = idx - window_start_idx
            
            # Pre-render caption PNG
            png_filename = f"caption_{idx}.png"
            png_path = os.path.join(temp_dir, png_filename)
            self.render_caption_frame(window_words, active_pos_in_window, png_path)
            
            # Create ImageClip for this exact word window
            sub_clip = (
                ImageClip(png_path)
                .set_start(start_t)
                .set_duration(end_t - start_t)
            )
            clips.append(sub_clip)
            
        # 5. Composite and export
        video = CompositeVideoClip(clips, size=(1080, 1920))
        video = video.set_audio(audio_clip)
        
        os.makedirs(os.path.dirname(os.path.abspath(output_video_path)), exist_ok=True)
        video.write_videofile(
            output_video_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None
        )
        
        # Clean up temp folder
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return output_video_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_video_agent.py::test_compose_video`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/my_automated_traffic/video_agent.py tests/test_video_agent.py
git commit -m "feat: implement final MoviePy video stitching and overlays"
```
