import chromadb
from chromadb.utils.embedding_functions.ollama_embedding_function import (
    OllamaEmbeddingFunction,
)
from typing import List, Dict, Any


class MC_RAG:
    _id_counter = 0

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

    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to the collection"""
        start_id = MC_RAG._id_counter
        ids = [str(start_id + i) for i in range(len(documents))]
        MC_RAG._id_counter += len(documents)
        texts = [doc["text"] for doc in documents]

        self.collection.add(
            ids=ids,
            documents=texts
        )

    def query(self, query_text: str, n_results: int = 3) -> List[Dict[str, Any]]:
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

    def generate_response(self, query_text: str, context: List[str]) -> str:
        """Generate a response using the retrieved context"""
        # Placeholder for actual LLM integration
        context_str = "\n".join(context)
        return f"Based on the context:\n{context_str}\n\nResponse to '{query_text}'"

    def rag_pipeline(self, query_text: str) -> str:
        """Complete RAG pipeline"""
        # Retrieve relevant documents
        retrieved_docs = self.query(query_text)
        context = [doc["text"] for doc in retrieved_docs]

        # Generate response
        return self.generate_response(query_text, context)


# Example usage
if __name__ == "__main__":
    rag = MC_RAG()

    # Add sample documents
    sample_docs = [
        {"text": "ChromaDB is a vector database for AI applications."},
        {"text": "RAG combines retrieval and generation for better AI responses."},
        {"text": "Embeddings are numerical representations of text."}
    ]
    rag.add_documents(sample_docs)

    # Query the system
    query = "What is ChromaDB?"
    response = rag.rag_pipeline(query)
    print(response)
