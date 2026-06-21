# Design Specification: AI Video Generation Agent (VideoAgent)

**Date**: 2026-06-21  
**Status**: Approved / Ready for Implementation  
**Feature**: Original SFW Video Creation using Imagen, Edge-TTS, and brand assets  

---

## 1. Goal & Requirements
The goal of this enhancement is to transform the `VideoAgent` from a simple script and TTS compiler into a fully functioning short-form video generator. To ensure originality and high click-through potential, the generator must:
1. **Generate Original Visuals**: Call Google GenAI SDK (Imagen) to generate a series of unique 9:16 vertical images relevant to each scene in the script.
2. **Dynamic TTS & Timestamps**: Use Microsoft Edge TTS to synthesize audio and retrieve word-by-word timestamps for caption synchronization.
3. **Stitch Visuals & Voiceover**: Use MoviePy to assemble the images, apply a dynamic Ken Burns effect (gradual pan/zoom), and overlay the audio.
4. **Incorporate Brand Assets**: Allow the overlay of user-provided brand logos (watermark) and specific campaign deliverables (product mockups) during the CTA scene.
5. **Render Dynamic Subtitles**: Programmatically burn kinetic, word-highlighted subtitles onto the video without requiring system ImageMagick binaries by pre-rendering text onto transparent frames using Pillow.

---

## 2. High-Level Flow

```
   ┌────────────────────────────────────────────────────────┐
   │                    Campaign Niche                      │
   └───────────────────────────┬────────────────────────────┘
                               │
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │            1. Structured Script Generation             │
   │ - Call LLM to return JSON containing Hook, Body, CTA,   │
   │   and Imagen image prompts for each scene.             │
   └───────────────────────────┬────────────────────────────┘
                               │
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │           2. Voiceover & Word-Level Timestamps         │
   │ - Use edge-tts to generate campaign voiceover MP3.     │
   │ - Retrieve exact start/end time offsets for each word.  │
   └───────────────────────────┬────────────────────────────┘
                               │
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │            3. Image Generation (Imagen API)             │
   │ - Loop scenes, request 9:16 vertical images via Imagen.│
   │ - Save image files locally under assets directory.     │
   └───────────────────────────┬────────────────────────────┘
                               │
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │            4. Video Assembly & Custom Overlays         │
   │ - Create VideoClips, apply Ken Burns transitions.      │
   │ - Render Pillow transparent subtitle clips.            │
   │ - Overlay logo and final product CTA images.           │
   │ - Render & export final SFW MP4.                       │
   └────────────────────────────────────────────────────────┘
```

---

## 3. Database Integration
The existing `video_assets` table schema is already fully compatible and will hold the generated files:
* `script_text`: The full generated script text.
* `audio_path`: Path to the synthesized TTS voiceover MP3 file.
* `video_path`: Path to the final stitched vertical MP4 file.
* `status`: Set to `generating` during the pipeline, and updated to `ready` once the MP4 is compiled.

---

## 4. Component Details & Interfaces

### 4.1 Script Structure
The LLM will be instructed to return a strict JSON format matching the niche's topic:
```json
{
  "scenes": [
    {
      "scene_number": 1,
      "voiceover_text": "HOOK text",
      "visual_prompt": "Prompt for Imagen to generate a 9:16 SFW background scene"
    },
    {
      "scene_number": 2,
      "voiceover_text": "BODY text",
      "visual_prompt": "Prompt for Imagen to generate a 9:16 SFW body scene"
    },
    {
      "scene_number": 3,
      "voiceover_text": "CTA text",
      "visual_prompt": "Prompt for Imagen to generate a 9:16 SFW CTA scene"
    }
  ]
}
```

### 4.2 Class: `VideoAgent`
The class `VideoAgent` in `src/my_automated_traffic/video_agent.py` will expose:

```python
class VideoAgent:
    def __init__(self, llm_client: Any, imagen_client: Any = None) -> None:
        self.llm_client = llm_client
        self.imagen_client = imagen_client

    def generate_structured_script(self, niche: str) -> Dict[str, Any]:
        """Prompts LLM (Gemini) to return structured JSON script scenes and image prompts."""

    async def generate_voiceover(self, text: str, output_audio_path: str) -> List[Dict[str, Any]]:
        """Synthesizes text using edge-tts. Returns list of word dictionaries with timestamps:
        [{"word": "Hello", "start": 0.0, "end": 0.3}]
        """

    def generate_scene_images(self, scenes: List[Dict[str, Any]], output_dir: str) -> List[str]:
        """Generates 9:16 vertical SFW images via Google GenAI Imagen model.
        Falls back to theme-colored gradient background image if Imagen fails.
        """

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
        """Assembles video via MoviePy:
        - Creates image clips with Ken Burns effects.
        - Pre-renders word-highlighted kinetic subtitles using Pillow transparent frames.
        - Watermarks logo on top-right.
        - Inserts deliverable mockup in the center during the CTA scene.
        - Merges audio and writes the final MP4.
        """
```

### 4.3 Captions Sub-Renderer
To avoid `ImageMagick` installation dependencies:
1. Determine the active word for any given timestamp from `word_timestamps`.
2. Generate transparent PNG frames with the text centered (using Python's `Pillow` library). The active word will be highlighted in yellow, while passive words are in white.
3. Import these frames as MoviePy `ImageClip` segments and overlay them on the main video clip sequence.

---

## 5. Error Handling & Robustness
1. **Imagen Safe For Work Check**: If Gemini blocks a visual prompt or Imagen returns safety flags, or the API call fails, the agent generates a custom elegant gradient image matching the niche theme using Pillow.
2. **File Cleanup**: Temporary voice files, individual scene frames, and subtitles PNGs are generated in a temporary directory and fully cleaned up once the final video is written or if execution crashes.

---

## 6. Testing Plan
1. **Unit Tests**: Add tests mocking `edge-tts` and `Imagen` services to assert correct parameter passing and fallback behavior.
2. **Video Composition Assertions**: Test code that creates a dummy video from basic color frames and checks that a valid `.mp4` is written to disk.
