import os
from ollama import Client
from openai import OpenAI
from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential


class LLMClient:
    def __init__(self, api_key, model):
        self.api_key = api_key
        self.model = model
        self.client = None

    def chat(self, user_message):
        raise NotImplementedError


class OpenAIClient(LLMClient):
    def __init__(self,
                 api_key=os.getenv("OPENAI_API_KEY"),
                 model="gpt-4o-mini"
                 ):
        super().__init__(api_key, model)
        self.client = OpenAI(api_key)

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
    def __init__(self,
                 api_key=os.getenv("OLLAMA_API_KEY"),
                 model="qwen2.5:latest"
                 ):
        super().__init__(api_key, model)
        self.client = Client()

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
    def __init__(self,
                 api_key=os.getenv("GOOGLE_API_KEY"),
                 model="gemini-2.0-flash-lite-preview-02-05"
                 ):
        super().__init__(api_key, model)
        self.client = genai.Client(api_key=api_key)

        @retry(stop=stop_after_attempt(60), wait=wait_exponential(multiplier=1, min=1, max=60))
        def chat(self, user_message):
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[user_message])
            return response.text.strip()


class SiliconFlowClient(LLMClient):
    def __init__(self,
                 api_key=os.getenv("SILICONFLOW_API_KEY"),
                 model="Qwen/Qwen2.5-32B-Instruct"
                 ):
        super().__init__(api_key, model)
        self.client = OpenAI(api_key=api_key,
                             base_url="https://api.siliconflow.cn/v1")

    @retry(stop=stop_after_attempt(60), wait=wait_exponential(multiplier=1, min=1, max=60))
    def chat(self, user_message):
        messages = [
            {
                "role": "user",
                "content": user_message
            }
        ]

        response = self.client.chat.completions.create(
            messages=messages,
            model=self.model,
        )

        return response.choices[0].message.content.strip()


if __name__ == "__main__":
    siliconflow_client = SiliconFlowClient()
    print(siliconflow_client.chat("Why is the sky blue?"))
