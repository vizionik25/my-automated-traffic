import os
import json
from typing import Dict, Any, List
import edge_tts
from gtts import gTTS
from PIL import Image, ImageDraw


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

