import os
from gtts import gTTS

class VideoAgent:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def generate_script(self, niche):
        prompt = f"Write a short, engaging 30-second TikTok script about {niche} advice. Must contain 'Hook:', 'Body:', and 'CTA: link in bio'."
        return self.llm_client.generate(prompt)

    def generate_audio(self, text, output_path):
        tts = gTTS(text=text, lang='en')
        tts.save(output_path)
        return output_path
