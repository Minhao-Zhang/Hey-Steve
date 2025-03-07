import chromadb
from chromadb.utils.embedding_functions.ollama_embedding_function import (
    OllamaEmbeddingFunction,
)
from typing import List, Dict, Any
from .reranker import Reranker
from tqdm import tqdm
import requests


class SteveRAG:
    """
    A class for implementing Retrieval Augmented Generation (RAG)
    using ChromaDB for document storage and retrieval.
    """

    def __init__(self,
                 collection_name: str = "mc_rag",
                 ollama_embed_model: str = "snowflake-arctic-embed2:latest",
                 reranker: Reranker = None):
        """
        Initializes the SteveRAG with ChromaDB client, embedding function, and reranker.

        Args:
            collection_name (str): The name of the ChromaDB collection.
            ollama_embed_model (str): The name of the Ollama embedding model.
            reranker (Reranker, optional): A reranker object for reranking the results. Defaults to None.
        """

        self.reranker = reranker
        self.client = chromadb.PersistentClient()
        self.embedding_fn = OllamaEmbeddingFunction(
            url="http://localhost:11434/api/embeddings",
            model_name=ollama_embed_model,
        )

        try:
            response = requests.get("http://localhost:11434/api/ps", timeout=3)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        except requests.ConnectionError:
            print("Warning: Ollama server is not running on http://localhost:11434.")
        except requests.HTTPError as e:
            print(f"Warning: Ollama server returned an error: {e}")
        except requests.Timeout:
            print("Warning: Ollama server timed out on http://localhost:11434.")

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )
        self._id_counter = self.collection.count()

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Add documents to the collection

        Args:
            documents: List of document dictionaries containing 'text' and optional 'metadata'
        """
        start_id = self._id_counter
        ids = [str(start_id + i) for i in range(len(documents))]
        self._id_counter += len(documents)
        texts = [doc["text"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]

        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )

    def query(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Query the collection and return relevant documents.

        Args:
            query_text (str): The query text.
            n_results (int): The number of results to return.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the retrieved documents and their metadata.
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )

        return [
            {
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            }
            for i in range(len(results["documents"][0]))
        ]

    def query_with_reranking(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Query the collection, rerank the results, and return the top documents.

        Args:
            query_text (str): The query text.
            n_results (int): The number of results to return after reranking.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the top reranked documents and their metadata.
        """
        # Initial retrieval of more documents
        results = self.query(query_text, n_results=15)
        if self.reranker:
            # Rerank the results using the provided reranker
            reranked_results = self.reranker.rerank(query_text, results)
            top_results = reranked_results[:n_results]
        else:
            # If no reranker is provided, return the top n_results from the initial retrieval
            top_results = results[:n_results]

        return top_results

    def load_chunks_into_rag(self, chunks_dir: str = "data/chunks") -> None:
        """Loads JSON chunks from files in the specified directory into the RAG.

        Args:
            chunks_dir (str): The directory containing the JSON chunk files.
        """
        import os
        import json

        files = [f for f in os.listdir(chunks_dir) if f.endswith('.json')]

        for filename in tqdm(files, desc="Inserting directory of chunks"):
            filepath = os.path.join(chunks_dir, filename)
            with open(filepath, 'r') as f:
                data = json.load(f)
                if data:
                    documents = [{"text": item, "metadata": {
                        "source": filename}} for item in data]
                    self.add_documents(documents)
