from mc_ai_assistant.rag import MC_RAG
from mc_ai_assistant.utils import *
from mc_ai_assistant.agent import MC_Agent

mc_rag = MC_RAG()
llm_client = OllamaClient(model="llama3.2:latest")
# llm_client = GeminiClient()
# mc_rag.load_chunks_into_rag()
mc_agent = MC_Agent(mc_rag, llm_client)

while True:
    text = input(
        "Ask me anything about MineCraft (type `exit` to quit): ").strip()
    if text == "exit":
        print("Exiting...")
        break

    print(mc_agent.chat(text))
    print("="*80)
