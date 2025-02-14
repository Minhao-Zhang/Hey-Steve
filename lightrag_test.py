from lightrag.utils import EmbeddingFunc
from lightrag.llm.ollama import ollama_model_complete, ollama_embed
import os
from lightrag import LightRAG, QueryParam
from get_page_names import gen_name_list

#########
import nest_asyncio
nest_asyncio.apply()
#########

WORKING_DIR = "./dickens"

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)


# Initialize LightRAG with Ollama model
rag = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=ollama_model_complete,  # Use Ollama model for text generation
    llm_model_name='llama3.2:latest',  # Your model name
    # Use Ollama embedding function
    embedding_func=EmbeddingFunc(
        embedding_dim=768,
        max_token_size=8192,
        func=lambda texts: ollama_embed(
            texts,
            embed_model="nomic-embed-text"
        )
    ),
)

mobs = gen_name_list('urls/mobs.txt')
blocks = gen_name_list('urls/blocks.txt')
items = gen_name_list('urls/items.txt')

pages = mobs + blocks + items
for page in pages:
    with open(f"data/{page}.md", "r") as f:
        rag.insert(f.read())
