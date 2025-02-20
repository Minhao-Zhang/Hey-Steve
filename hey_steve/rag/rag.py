import chromadb
from chromadb.utils.embedding_functions.ollama_embedding_function import (
    OllamaEmbeddingFunction,
)
from typing import List, Dict, Any


class SteveRAG:
    # this shall be changed the next time I embed
    def __init__(self, collection_name: str = "mc_rag"):
        self.client = chromadb.PersistentClient()
        self.embedding_fn = OllamaEmbeddingFunction(
            # this shall be changed in the near future.
            url="http://localhost:11434/api/embeddings",
            model_name="snowflake-arctic-embed2:latest",
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )
        self._id_counter = self.collection.count()

    def add_documents(self, documents: List[str]):
        """Add documents to the collection"""
        start_id = self._id_counter
        ids = [str(start_id + i) for i in range(len(documents))]
        self._id_counter += len(documents)
        texts = [doc["text"] for doc in documents]

        self.collection.add(
            ids=ids,
            documents=texts
        )

    def query(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Query the collection and return relevant documents"""
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

    def retrieve_docs(self, query_text: str, n_results: int = 5) -> List[str]:
        # Retrieve relevant documents
        retrieved_docs = self.query(query_text, n_results=n_results)
        context = [doc["text"] for doc in retrieved_docs]

        return context

    def load_chunks_into_rag(self, chunks_dir="data/chunks"):
        """Loads JSON chunks from files in the specified directory into the RAG."""
        import os
        import json

        files = [f for f in os.listdir(chunks_dir) if f.endswith('.json')]
        total_files = len(files)

        for i, filename in enumerate(files):
            filepath = os.path.join(chunks_dir, filename)
            print(f"Processing {filename} ({i+1}/{total_files})")

            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)

                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, str):
                                # Assuming MC_RAG has an add method
                                self.add_documents([{"text": item}])
                            else:
                                print(
                                    f"Warning: Skipping non-string item in {filename}: {item}")
                    else:
                        print(f"Warning: Skipping non-list data in {filename}")

            except FileNotFoundError:
                print(f"Error: File not found: {filepath}")
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON in {filepath}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")
