import json
import re
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


def split_markdown_table(table_string, max_chunk_length=1000):
    """
    Splits a markdown table string into chunks based on character length of *table content*,
    adding the table header to each chunk. The final chunk size might exceed 600 due to header.

    Args:
        table_string (str): A string containing only the markdown table.

    Returns:
        list: A list of strings, where each string is a chunk of the table
              with the table header prepended. The *content* portion of each chunk
              (excluding header) is aimed to be within 600 characters.
    """

    chunks = []
    current_chunk = ""
    current_chunk_content_length = 0  # Track content length, excluding header
    lines = table_string.splitlines(keepends=True)

    if len(lines) < 2:
        # Return as single chunk if no proper header
        return [f"{''.join(lines)}"]

    header_lines = lines[:2]  # Extract the header (first two lines)
    body_lines = lines[2:]    # The rest are considered body lines

    header_text = "".join(header_lines)

    for line in body_lines:  # Iterate only through the body lines now
        line_length = len(line)

        if current_chunk_content_length + line_length <= max_chunk_length:
            current_chunk += line
            current_chunk_content_length += line_length  # Update content length
        else:
            if current_chunk:
                # Add header and then the current chunk body
                chunks.append(f"{header_text}{current_chunk}")
            current_chunk = line
            current_chunk_content_length = line_length  # Reset content length

    if current_chunk:  # Add the last chunk
        chunks.append(f"{header_text}{current_chunk}")

    return chunks


def chunk_text(text: str, max_length: int = 1100) -> list[str]:
    """
    Splits a given text into chunks, prioritizing double newlines for paragraphs.
    If necessary, falls back to sentence-based splitting.

    Args:
        text (str): The input text to split.
        max_length (int): The maximum allowed length per chunk.

    Returns:
        list[str]: A list of chunked text pieces.
    """
    chunks = []
    current_chunk = ""

    # Split by **paragraphs** (double newline) first
    paragraphs = text.split("\n\n")
    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= max_length:  # +2 for "\n\n"
            current_chunk += (para + "\n\n")
        else:
            if current_chunk:  # Save the current chunk
                chunks.append(current_chunk.strip())
                current_chunk = ""

            # If a paragraph is still too long, break it by sentences
            if len(para) > max_length:
                # Split by sentence
                sentences = re.split(r"(?<=[.!?])\s+", para)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 <= max_length:
                        current_chunk += (sentence + " ")
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            current_chunk = ""
                        current_chunk = sentence + " "  # Start a new chunk
            else:
                current_chunk = para + "\n\n"  # Start a new chunk

    if current_chunk:
        chunks.append(current_chunk.strip())  # Append last chunk

    return chunks


def replace_chunk_tags(md_content):
    """
    Replaces <chunk> </chunk> tag pairs in a string with numbered <chunk__XXX> </chunk_XXX> tags.

    Args:
        md_content: The input string containing md content with <chunk> </chunk> tags.

    Returns:
        A string with the <chunk> </chunk> tags replaced by numbered tags.
    """
    counter = 1
    output_content = ""
    start_index = 0

    while True:
        start_tag_index = md_content.find("<chunk>", start_index)
        if start_tag_index == -1:
            # No more <chunk> tags found, append the rest of the content
            output_content += md_content[start_index:]
            break

        end_tag_index = md_content.find(
            "</chunk>", start_tag_index + len("<chunk>"))
        if end_tag_index == -1:
            # This should not happen based on the problem description (always in pairs)
            # But as a safety net, handle it - maybe just append the rest as is.
            output_content += md_content[start_index:]
            break

        # Append the content before the current <chunk> tag
        output_content += md_content[start_index:start_tag_index]

        # Construct the new tags with counter
        # Format counter to 3 digits e.g., 001, 002, ...
        chunk_number_str = str(counter).zfill(3)
        new_start_tag = f"<chunk__{chunk_number_str}>"
        new_end_tag = f"</chunk_{chunk_number_str}>"

        output_content += new_start_tag
        # Content inside the tags, if any. (Though in example, tags seem empty)
        output_content += md_content[start_tag_index +
                                     len("<chunk>"):end_tag_index]
        output_content += new_end_tag

        # Update start_index to search for the next pair after the current </chunk> tag
        start_index = end_tag_index + len("</chunk>")
        counter += 1

    return output_content


def generate_chunk_json_template(num_chunks):
    """
    Generates a JSON-formatted string with numbered chunks.

    Args:
        num_chunks: The number of chunks to generate.

    Returns:
        A JSON-formatted string representing a dictionary of chunks with default context messages.
    """
    chunk_dict = {}
    for i in range(1, num_chunks + 1):
        chunk_number_str = str(i).zfill(3)
        chunk_key = f"chunk_{chunk_number_str}"
        chunk_value = f"Your short context for chunk_{chunk_number_str}"
        chunk_dict[chunk_key] = chunk_value

    # indent=2 for pretty printing, optional
    json_output = json.dumps(chunk_dict, indent=2)
    return json_output
