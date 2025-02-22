import readline
from hey_steve.agent.agent import HeySteve
from hey_steve.LLMs.LLMClient import OllamaClient
from hey_steve.rag.rag import SteveRAG


# Initialize components
llm_client = OllamaClient(model="llama3.2:latest")
rag = SteveRAG()
agent = HeySteve(steve_rag=rag, llm_client=llm_client)

print("Hey I am Steve. Type your queries below (type 'exit' to quit):")

while True:
    query = input("\nQuery: ")
    if query.lower() == 'exit':
        break

    response = agent.chat(query)
    print(f"\nResponse: {response}")
