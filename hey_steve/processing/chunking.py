"""Module for processing and chunking markdown files into smaller, structured pieces."""

import json
from pathlib import Path
from typing import List, Dict, Any

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
    TextSplitter,
)
import tiktoken

# Constants
HEADERS_TO_SPLIT_ON = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

MIN_TOKENS_FOR_SPLIT = 150
SEPARATORS = ["\n\n", "\n", ".", "?", "!", " ", ""]

# Initialize paths
INPUT_DIR = Path("data/md")
SAVE_DIR = Path("data/chunks")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# Initialize text splitters
splitter: MarkdownHeaderTextSplitter = MarkdownHeaderTextSplitter(
    HEADERS_TO_SPLIT_ON)
tokenizer = tiktoken.get_encoding("cl100k_base")

rcts: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
    separators=SEPARATORS,
    keep_separator=False,
)


def construct_header_string(chunk: Dict[str, Any]) -> str:
    """
    Constructs a header string based on metadata.

    Args:
        chunk: Dictionary containing chunk metadata and content

    Returns:
        str: Formatted header string
    """
    headers = []
    if "Header 1" in chunk.metadata:
        headers.append(f"{chunk.metadata['Header 1']}")
    if "Header 2" in chunk.metadata:
        headers.append(f"section {chunk.metadata['Header 2']}")
    if "Header 3" in chunk.metadata:
        headers.append(f"subsection {chunk.metadata['Header 3']}")

    return f"Content of {' > '.join(headers)}. " if headers else ""


def process_markdown_file(filepath: Path) -> None:
    """
    Processes a markdown file and saves chunked output as JSON.

    Args:
        filepath: Path to the markdown file to process
    """
    try:
        print(f"Processing file: {filepath.name}")

        with filepath.open("r", encoding="utf-8") as f:
            text = f.read()

        header_chunks = splitter.split_text(text)
        chunks: List[str] = []

        for chunk in header_chunks:
            header_string = construct_header_string(chunk)
            num_tokens = len(tokenizer.encode(chunk.page_content))

            if num_tokens > MIN_TOKENS_FOR_SPLIT:
                split_chunks = rcts.split_text(chunk.page_content)
                modified_split_chunks = [
                    header_string + sc for sc in split_chunks]
                chunks.extend(modified_split_chunks)
            else:
                chunks.append(header_string + chunk.page_content)

        # Save processed chunks
        output_filepath = SAVE_DIR / f"{filepath.stem}.json"
        with output_filepath.open("w", encoding="utf-8") as outfile:
            json.dump(chunks, outfile, indent=4)

        print(f"Successfully processed {filepath.name}")

    except Exception as e:
        print(f"ERROR: Error processing {filepath.name}: {str(e)}")
        raise


def main() -> None:
    """Main function to process all markdown files in the input directory."""
    print("Starting markdown processing")

    for file in INPUT_DIR.glob("*.md"):
        try:
            process_markdown_file(file)
        except Exception as e:
            print(f"ERROR: Failed to process {file.name}: {str(e)}")
            continue

    print("Markdown processing completed")


if __name__ == "__main__":
    main()
