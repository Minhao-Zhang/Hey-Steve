import ollama
import openai
import google.genai as genai


def get_ollama_embedding(text: str, model="snowflake-arctic-embed2:latest") -> list[float]:
    """Get embedding for text using snowflake-arctic-embed2 model.

    Args:
        text: Input text to embed

    Returns:
        List of floats representing the embedding vector
    """
    response = ollama.embed(
        model=model,
        prompt=text
    )
    return response["embedding"]
