from langchain_text_splitters import MarkdownHeaderTextSplitter


def chunk_markdown(markdown_text):
    """
    Split markdown text into chunks based on headings (level 3 and above).

    Args:
        markdown_text (str): The markdown text to chunk

    Returns:
        list: List of strings containing the content of each block
    """
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on)
    return splitter.split_text(markdown_text)


def semantic_chunks(chunks):
    """
    Processes a list of markdown chunks using a given llm_client to perform semantic chunking.

    Args:
        chunks (list): A list of markdown chunks (strings).

    Returns:
        list: List of strings containing the semantically chunked text.
    """
    chunk_size = 1000
    processed_chunks = []
    for chunk in chunks:
        current_chunk = ""
        sentences = chunk.split(". ")  # Simple sentence splitting
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 <= chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    processed_chunks.append(current_chunk)
                current_chunk = sentence + ". "
        if current_chunk:
            processed_chunks.append(current_chunk)
    return processed_chunks
