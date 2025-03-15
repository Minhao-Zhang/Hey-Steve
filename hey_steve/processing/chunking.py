import json
from pathlib import Path
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
import tiktoken

# Define headers for markdown splitting
HEADERS_TO_SPLIT_ON = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]
splitter = MarkdownHeaderTextSplitter(HEADERS_TO_SPLIT_ON)

# Define paths
INPUT_DIR = Path("data/md")
SAVE_DIR = Path("data/chunks_custom")
SAVE_DIR.mkdir(parents=True, exist_ok=True)  # Ensure save directory exists

tokenizer = tiktoken.get_encoding("cl100k_base")


rcts = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=200,
    separators=["\n\n", "\n", ".", "?", "!", " ", ""],
    keep_separator=False
)


def construct_header_string(chunk) -> str:
    """Constructs a header string based on metadata."""
    headers = []
    if "Header 1" in chunk.metadata:
        headers.append(f"{chunk.metadata['Header 1']}")
    if "Header 2" in chunk.metadata:
        headers.append(f"section {chunk.metadata['Header 2']}")
    if "Header 3" in chunk.metadata:
        headers.append(f"subsection {chunk.metadata['Header 3']}")

    header_prefix = f"Content of {' > '.join(headers)}. " if headers else ""
    return header_prefix


def process_markdown_file(filepath: Path):
    """Processes a markdown file and saves chunked output as JSON."""
    with filepath.open("r", encoding="utf-8") as f:
        text = f.read()

    header_chunks = splitter.split_text(text)
    chunks = []

    for chunk in header_chunks:
        header_string = construct_header_string(chunk)
        num_tokens = len(tokenizer.encode(chunk.page_content))
        if num_tokens > 150:
            split_chunks = rcts.split_text(chunk.page_content)
            modified_split_chunks = [header_string + sc for sc in split_chunks]
            chunks.extend(modified_split_chunks)
        else:
            chunks.append(header_string + chunk.page_content)

    # Save processed chunks to a JSON file
    output_filepath = SAVE_DIR / f"{filepath.stem}.json"
    with output_filepath.open("w", encoding="utf-8") as outfile:
        json.dump(chunks, outfile, indent=4)


# Process all markdown files in the input directory
for file in INPUT_DIR.glob("*.md"):
    process_markdown_file(file)
