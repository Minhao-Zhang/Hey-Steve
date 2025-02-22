from hey_steve.rag import SteveRAG
from hey_steve.LLMs.LLMClient import LLMClient


class SteveAgent:
    def __init__(self,
                 steve_rag: SteveRAG,
                 llm_client: LLMClient,
                 response_template: str = "hey_steve/prompt_template/rag_response.txt"
                 ):

        self.steve_rag = steve_rag
        self.llm_client = llm_client
        with open(response_template, "r") as f:
            self.context_prompt_tempate = f.read()

    def chat(self, query: str, n_results: int = 5) -> str:
        context = self.steve_rag.retrieve_docs(query, n_results=n_results)
        user_prompt = self.context_prompt_tempate.format(
            context="\n".join(context), query=query)
        response = self.llm_client.chat(user_prompt)
        return response
