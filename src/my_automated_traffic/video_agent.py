import os
import json
import tempfile
import shutil
from typing import Dict, Any, List
import edge_tts
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
try:
    from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
except ImportError:
    from moviepy import ImageClip, AudioFileClip, CompositeVideoClip


class VideoAgent:
    """Agent responsible for generating short-form video scripts and voiceover audio."""

    def __init__(self, llm_client: Any, imagen_client: Any = None) -> None:
        """Initializes the VideoAgent with an LLM client and optional Imagen client.

        Args:
            llm_client: The LLM client used to generate scripts.
            imagen_client: The Imagen client used to generate images.
        """
        self.llm_client = llm_client
        self.imagen_client = imagen_client

    def generate_script(self, niche: str) -> str:
        """Generates a short-form video script for a given niche.

        Args:
            niche: The target niche/topic.

        Returns:
            The generated script text containing Hook, Body, and CTA.
        """
        prompt = (
            f"Write a short, engaging 30-second TikTok script about {niche} advice. "
            "Must contain 'Hook:', 'Body:', and 'CTA: link in bio'."
        )
        return self.llm_client.generate(prompt)

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

    def generate_audio(self, text: str, output_path: str, lang: str = "en") -> str:
        """Generates an MP3 audio file from text using gTTS.

        Args:
            text: The text to convert to speech.
            output_path: The filesystem path where the MP3 file will be saved.
            lang: Language code for text-to-speech. Defaults to 'en'.

        Returns:
            The path to the generated audio file.

        Raises:
            ValueError: If text or output_path is empty.
            RuntimeError: If gTTS generation or file saving fails.
        """
        if not text:
            raise ValueError("Text content cannot be empty.")
        if not output_path:
            raise ValueError("Output path cannot be empty.")

        # Ensure parent directories exist
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        try:
            tts = gTTS(text=text, lang=lang)
            tts.save(output_path)
        except Exception as e:
            raise RuntimeError(f"Failed to generate or save TTS audio: {e}") from e

        return output_path

    async def generate_voiceover(self, text: str, output_audio_path: str) -> List[Dict[str, Any]]:
        """Generates voiceover audio and returns word-level timestamps using edge-tts.

        This is the primary TTS method for the video pipeline.

        Args:
            text: The text to synthesize.
            output_audio_path: Output file path for the MP3 audio.

        Returns:
            A list of dictionaries with word, start, and end time.
        """
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
        for cue in submaker.cues:
            timestamps.append({
                "word": cue.content,
                "start": cue.start.total_seconds(),
                "end": cue.end.total_seconds()
            })
        return timestamps

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
                # Call the Imagen client
                result = self.imagen_client.generate_images(
                    prompt=f"{prompt}, high quality, cinematic lighting, safe for work, SFW",
                    number_of_images=1,
                    aspect_ratio="9:16"
                )
                image_bytes = result.generated_images[0].bytes
                with open(img_path, "wb") as f:
                    f.write(image_bytes)
            except Exception as e:
                # Fallback to Pillow gradient
                self._create_fallback_image(img_path)
                
            image_paths.append(img_path)
        return image_paths

    def _load_font(self, size: int) -> Any:
        """Finds and loads a readable TrueType font from system paths, falling back to default."""
        font_paths = []
        if os.name == "nt":  # Windows
            windir = os.environ.get("WINDIR", "C:\\Windows")
            font_paths.extend([
                os.path.join(windir, "Fonts", "arial.ttf"),
                os.path.join(windir, "Fonts", "calibri.ttf")
            ])
        elif os.uname().sysname == "Darwin":  # macOS
            font_paths.extend([
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/Supplemental/Courier New.ttf",
                "/Library/Fonts/Arial.ttf"
            ])
        else:  # Linux/Unix
            font_paths.extend([
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
            ])
            
        for path in font_paths:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue
                    
        # Try loading by name directly using PIL search
        for name in ["arial.ttf", "Arial.ttf", "Helvetica.ttf", "DejaVuSans.ttf"]:
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                continue

        # Ultimate fallback
        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()

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
        
        font = self._load_font(48)
            
        # Draw words centered horizontally, active word highlighted
        text_y = height // 2
        total_width = 0
        word_spacings = []
        
        for w in words:
            # Estimate text width
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
        audio_clip = None
        video = None
        clips = []
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Determine total duration from audio
            audio_clip = AudioFileClip(audio_path)
            total_duration = audio_clip.duration
            
            # Calculate duration per scene
            scene_duration = total_duration / len(scenes)
            
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
                
                # Determine stationary non-overlapping window slice
                chunk_idx = idx // window_size
                window_start_idx = chunk_idx * window_size
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
            
            return output_video_path
            
        finally:
            # Call clip.close() on all clips to prevent fd leaks
            for clip in clips:
                try:
                    clip.close()
                except Exception:
                    pass
            if video is not None:
                try:
                    video.close()
                except Exception:
                    pass
            if audio_clip is not None:
                try:
                    audio_clip.close()
                except Exception:
                    pass
                    
            # Clean up temp folder
            shutil.rmtree(temp_dir, ignore_errors=True)



