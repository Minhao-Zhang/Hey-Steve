import os
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
import numpy as np


async def llm_model_func(
    prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs
) -> str:
    return await openai_complete_if_cache(
        "gemini-2.0-flash",
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        api_key=os.getenv("GOOGLE_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        **kwargs
    )


async def embedding_func(texts: list[str]) -> np.ndarray:
    return await openai_embed(
        texts,
        model="text-embedding-004",
        api_key=os.getenv("GOOGLE_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )


#########
# Uncomment the below two lines if running in a jupyter notebook to handle the async nature of rag.insert()
# import nest_asyncio
# nest_asyncio.apply()
#########

WORKING_DIR = "./dickens"

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

rag = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=llm_model_func,
    embedding_func=EmbeddingFunc(
        embedding_dim=768,
        max_token_size=8192,
        func=embedding_func
    )
)

with open("./book.txt") as f:
    rag.insert(f.read())


# Perform mix search (Knowledge Graph + Vector Retrieval)
# Mix mode combines knowledge graph and vector search:
# - Uses both structured (KG) and unstructured (vector) information
# - Provides comprehensive answers by analyzing relationships and context
# - Supports image content through HTML img tags
# - Allows control over retrieval depth via top_k parameter
print(rag.query("What are the top themes in this story?", param=QueryParam(
    mode="mix")))
