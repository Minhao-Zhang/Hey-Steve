import os
import ollama
import openai
import google


class LLMClient:
    def __init__(self, api_key, model):
        self.api_key = api_key
        self.model = model
        self.client = None

    def chat(self, user_message):
        raise NotImplementedError


class OpenAIClient(LLMClient):
    def __init__(self, api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o-mini"):
        super().__init__(api_key, model)
        self.client = openai.OpenAI(api_key)

    def chat(self, user_message):
        messages = [
            {
                "role": "user",
                "content": user_message
            }
        ]

        response = self.llm_client.chat.completions.create(
            messages=messages,
            model=self.model,
        )

        return response.choices[0].message.content.strip()


class OllamaClient(LLMClient):
    def __init__(self, api_key=os.getenv("OPENAI_API_KEY"), model="qwen2.5:latest"):
        super().__init__(api_key, model)
        self.client = ollama.Client()

    def chat(self, user_message):
        messages = [
            {
                "role": "user",
                "content": user_message
            }
        ]

        options = {
            "num_ctx": 1024*4,
        }

        response = self.llm_client.chat(
            model=self.model,
            messages=messages,
            options=options
        )

        return response['message']['content'].strip()


class GeminiClient(LLMClient):
    def __init__(self, api_key=os.getenv("GOOGLE_API_KEY"), model="gemini-2.0-flash-lite-preview-02-05"):
        super().__init__(api_key, model)
        self.client = google.Gemini(api_key)

    def chat(self, user_message):
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[user_message])
        return response.text.strip()
