from mc_ai_assistant.rag.rag import MC_RAG
from mc_ai_assistant.utils.LLMClient import LLMClient


class MC_Agent:
    def __init__(self, mc_rag: MC_RAG, llm_client: LLMClient):
        self.mc_rag = mc_rag
        self.llm_client = llm_client

    def chat(self, query: str) -> str:
        user_prompt = self.mc_rag.rag_pipeline(query)
        response = self.llm_client.chat(user_prompt)
        return response
