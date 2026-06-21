import os
import json
from typing import Dict, Any
from gtts import gTTS

class VideoAgent:
    """Agent responsible for generating short-form video scripts and voiceover audio."""

    def __init__(self, llm_client: Any) -> None:
        """Initializes the VideoAgent with an LLM client.

        Args:
            llm_client: The LLM client used to generate scripts.
        """
        self.llm_client = llm_client

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
