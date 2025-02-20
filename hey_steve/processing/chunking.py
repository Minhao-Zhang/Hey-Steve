from hey_steve.processing.extract_heading_info import extract_sections, extract_table, parse_json_to_markdown
from hey_steve.processing.contextual_embedding import get_context_for_chunk
import os
import json


def process_files(llm_client):
    """
    Processes markdown files in the raw_md directory, extracts information,
    chunks the content, adds context, and saves the chunks to JSON files.
    """
    directory = "."
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
        process_markdown_file(llm_client, filename)


def process_markdown_file(llm_client, filename):
    """
    Processes a single markdown file, extracts information,
    chunks the content, adds context, and saves the chunks to JSON files.
    """
    directory = "."

    # Check if the chunk file already exists
    chunks_dir = os.path.join(directory, "data/chunks")
    if not os.path.exists(chunks_dir):
        os.makedirs(chunks_dir)
    chunks_file_path = os.path.join(chunks_dir, f"{filename[:-3]}.json")
    if os.path.exists(chunks_file_path):
        print(
            f"Skipping file: {filename} - Using cached chunks at {chunks_file_path}")
        return

    print(f"Processing file: {filename}")
    filepath = os.path.join(directory, f"data/raw_md/{filename}")
    try:
        with open(filepath, "r") as f:
            md_content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return  # Skip to the next file

    # Grab the information on the top of page as they need special attention
    try:
        title, disambiguation, table_text, description, rest = extract_sections(
            md_content
        )

        # Modify md_content
        if title and rest:
            md_content = f"{title}\n{rest}"
        else:
            md_content = md_content

        table_json_string = None
        try:
            table_json_string = extract_table(table_text, llm_client)
            table_md = parse_json_to_markdown(table_json_string)
            # md_content = title + "\n" + disambiguation + "\n" + table_md + "\n" + rest # Removing this line
        except Exception as e:
            print(f"Error extracting table: {e}")

        if table_json_string:
            process_table(directory, filename, table_json_string)

        title_short = title[2:] if len(title) > 2 else title
        table_property = f"{title} has property of {table_md}" if table_md else f"{title} has property of {table_text}"
        chunks = [
            f"{title_short} has disambiguation information of {disambiguation}",
            table_property,
            description,
        ]

        # chunks = chunk_markdown(md_content) # Commenting out the original chunking
        # chunks = [c.page_content for c in chunks]

        contextual_chunks = []
        for chunk in chunks:  # Using the new chunks
            context = get_context_for_chunk(llm_client, md_content, chunk)
            contextual_chunks.append(f"{context}\n{chunk}")

        chunks_dir = os.path.join(directory, "data/chunks")
        chunks_file_path = os.path.join(
            chunks_dir, f"{filename[:-3]}.json")
        with open(chunks_file_path, "w") as outfile:
            json.dump(contextual_chunks, outfile, indent=4)
        print(f"Saved chunks to {chunks_file_path}")

    except Exception as e:
        print(f"Error processing file {filename}: {e}")


def process_table(directory, filename, table_json_string):
    """
    Extracts and saves table data to a JSON file.
    """
    properties_dir = os.path.join(directory, "data/properties")
    properties_file_path = os.path.join(
        properties_dir, f"{filename[:-3]}.json"
    )

    try:
        table_json = json.loads(table_json_string)
        with open(properties_file_path, "w") as outfile:
            json.dump(table_json, outfile, indent=4)
        print(f"Saved table to {properties_file_path}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except Exception as e:
        print(f"Error saving table to file: {e}")
