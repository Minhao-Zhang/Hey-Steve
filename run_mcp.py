import os
from mcp.server.fastmcp import FastMCP
from chromadb.utils.embedding_functions.sentence_transformer_embedding_function import SentenceTransformerEmbeddingFunction
from hey_steve.rag.rag import SteveRAG
# fastmcp dev run_mcp.py


mcp = FastMCP("Hey-Steve")

# reranker = Reranker()
steve_rag = SteveRAG(
    collection_name="mc_rag_custom",
    embedding_function=SentenceTransformerEmbeddingFunction(
        "nomic-ai/nomic-embed-text-v2-moe", trust_remote_code=True),
)

recipe_files = [f.replace(".json", "") for f in os.listdir(
            "data/mc/recipe") if f.endswith('.json')]

@mcp.tool()
def mc_kownlege_base(query: str, n_results: int = 5):
    """Retrieve semantically related documents to the querey"""
    
    docs = steve_rag.query_with_reranking(query, n_results=n_results)
    return "\nRetrieved documents:\n" + "".join(
        [f"\n\n===== Document {str(i)} =====\n" +
            doc['text'].replace("search_document: ", "") for i, doc in enumerate(docs)]
    )

@mcp.tool()
def recipe_lookup(item_name: str):
    """Retrieve the crafting recipe for an item in Minecraft"""
    item_name = item_name.lower()

    if item_name in recipe_files:
        with open(os.path.join("data/mc/recipe", item_name + ".json"), "r") as f:
            return f"The crafting recipe for {item_name} is \n" + f.read() + \
                "\n The pattern represents a 3x3 crafting table grid. \
                    If pattern does not show all 9 positions, if can be in any position while maintian the exact shape."
    else:
        item_name_parts = item_name.split("_")
        possible_matches = set()
        for part in item_name_parts:
            for recipe in recipe_files:
                if part in recipe:
                    possible_matches.add(recipe.strip(".json"))

        return f"No exact match is found, but here are a list of possible matches:" + ", ".join(possible_matches)
