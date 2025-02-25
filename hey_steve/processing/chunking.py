import hey_steve.processing.process_intro as intro
import hey_steve.processing.process_body as body
import hey_steve.processing.contextual_embedding as ctx_chunk
import hey_steve.processing.split_chunks as split_chunks
import os
import json


def process_introduction(llm_client, directory, filename, md_content):
    """
    Processes the introduction section of a markdown file, extracts information,
    and returns the processed title, property chunks, modified markdown content,
    and table JSON string.
    """
    # Grab the information on the top of page as they need special attention
    title, disambiguation, table_text, description, rest = intro.extract_sections(
        md_content
    )

    # Modify md_content
    if title and rest:
        md_content = f"{title}\n{rest}"
    else:
        md_content = md_content

    table_json_string = None
    try:
        table_json_string = intro.extract_property(table_text, llm_client)
        table_md = intro.parse_json_to_markdown(table_json_string)
    except Exception as e:
        print(f"Error extracting table: {e}")

    if table_json_string:
        from hey_steve.processing.process_intro import save_property
        save_property(directory, filename, table_json_string)

    title_short = title[2:] if len(title) > 2 else title
    table_property = f"{title} has property of {table_md}" if table_md else f"{title} has property of {table_text}"
    property_chunks = [
        f"{title_short} has disambiguation information of {disambiguation}",
        table_property,
        description,
    ]

    return title, property_chunks, md_content, table_json_string


def process_markdown_file(llm_client, filename, chunks_dir, chunks_file_path):
    """
    Processes a single markdown file, extracts information,
    chunks the content, adds context, and saves the chunks to JSON files.
    """
    directory = "."

    print(f"Processing file: {filename}")
    filepath = os.path.join(directory, f"data/raw_md/{filename}")
    try:
        with open(filepath, "r") as f:
            md_content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return  # Skip to the next file

    title, property_chunks, md_content, table_json_string = process_introduction(
        llm_client, directory, filename, md_content)

    # Commenting out the original chunking
    chunks = split_chunks.chunk_markdown(md_content)
    chunks = property_chunks.extend([c.page_content for c in chunks])

    contextual_chunks = []
    for chunk in chunks:  # Using the new chunks
        if ("|" in chunk and "---" in chunk):
            body.extract_table()

        context = ctx_chunk.get_context_for_chunk(
            llm_client, md_content, chunk)
        contextual_chunks.append(f"{context}\n{chunk}")

    with open(chunks_file_path, "w") as outfile:
        json.dump(contextual_chunks, outfile, indent=4)
    print(f"Saved chunks to {chunks_file_path}")


def process_files(llm_client):
    """
    Processes markdown files in the raw_md directory, extracts information,
    chunks the content, adds context, and saves the chunks to JSON files.
    """
    directory = "."

    # Create chunks directory if it doesn't exist
    chunks_dir = os.path.join(directory, "data/chunks")
    if not os.path.exists(chunks_dir):
        os.makedirs(chunks_dir)

    raw_md_path = os.path.join(directory, "data/raw_md")
    if not os.path.exists(raw_md_path):
        filenames = []
    else:
        filenames = [
            f
            for f in os.listdir(raw_md_path)
            if os.path.isfile(os.path.join(raw_md_path, f))
        ]

    filenames = sorted(filenames)

    for filename in filenames:
        chunks_file_path = os.path.join(chunks_dir, f"{filename[:-3]}.json")
        if os.path.exists(chunks_file_path):
            print(
                f"Skipping file: {filename} - Using cached chunks at {chunks_file_path}")
            continue
        process_markdown_file(llm_client, filename,
                              chunks_dir, chunks_file_path)
