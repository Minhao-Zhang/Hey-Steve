import argparse
import json
import os
import re
import time

from litellm import completion
from .chunking_helper import *


def process_md_file(md_content, max_length=1100):
    header_chunks = chunk_markdown(md_content)

    final_md = ""
    previous_headings = []  # Track previously seen headings
    all_chunks = []  # Store all valid chunks separately

    for chunk in header_chunks:
        metadata = chunk.metadata
        page_content = chunk.page_content

        # Extract ordered headings
        headings = []
        # Ensure metadata is processed in order
        for level in sorted(metadata.keys()):
            headings.append(metadata[level])

        # Identify the last new heading
        differing_index = 0
        for i, heading in enumerate(headings):
            if i >= len(previous_headings) or previous_headings[i] != heading:
                differing_index = i
                break

        # Add only new headings
        for new_heading in headings[differing_index:]:
            final_md += f"{'#' * (differing_index + 1)} {new_heading}\n"
            differing_index += 1  # Increase heading level

        previous_headings = headings  # Update tracked headings

        # Process content with multiple tables
        table_pattern = re.compile(r"<md_table>(.*?)</md_table>", re.DOTALL)
        # Splits text at every table occurrence
        parts = table_pattern.split(page_content)

        for i, part in enumerate(parts):
            # Non-table content (before, between, or after tables)
            if i % 2 == 0:
                stripped_part = part.strip()
                if stripped_part:
                    text_chunks = chunk_text(stripped_part, max_length)
                    for text_chunk in text_chunks:
                        if len(text_chunk) >= 20:  # **Discard chunks < 20 characters**
                            chunk_text_str = f"<chunk>\n{text_chunk}\n</chunk>\n\n"
                            final_md += chunk_text_str
                            all_chunks.append(text_chunk)

            else:  # This is a table (since it's between split results)
                # Split large tables if necessary
                table_chunks = split_markdown_table(part)
                for table_chunk in table_chunks:
                    if len(table_chunk) >= 20:  # **Discard small table chunks**
                        chunk_text_str = f"<chunk>\n{table_chunk}\n</chunk>\n\n"
                        final_md += chunk_text_str
                        all_chunks.append(table_chunk)

    final_md = replace_chunk_tags(final_md)

    json_tempate = generate_chunk_json_template(len(all_chunks))

    # with open("temp.md", "w") as f:
    #     f.write(final_md)

    with open("hey_steve/prompt_template/multi_context_chunk.txt", "r") as f:
        pt = f.read()

    messages = [
        {"role": "user",
         "content": pt.format(md_content=final_md, json_string=json_tempate)
         }
    ]

    response = completion(model="gemini/gemini-2.0-flash-thinking-exp-01-21",
                          api_key=os.environ['GEMINI_API_KEY'],
                          messages=messages
                          )
    time.sleep(2)

    response_string = response.choices[0].message.content
    response_string = response_string[7:-4]
    contexts = json.loads(response_string)

    assert len(contexts) == len(all_chunks)

    context_chunks = []
    for i, v in enumerate(all_chunks):
        context_chunks.append(contexts['chunk_' + str(i+1).zfill(3)] + v)

    return context_chunks


def process_md_directory(md_dir="data/md", chunk_dir="data/chunks"):
    """
    Reads all .md files in the specified directory, processes them using process_md_file,
    and saves the resulting chunks as JSON in another directory.

    Args:
        md_dir (str): Directory containing markdown files.
        chunk_dir (str): Directory to save processed chunks.

    Returns:
        list[str]: A list of all processed chunks.
    """
    # Ensure the chunk directory exists
    os.makedirs(chunk_dir, exist_ok=True)

    # Iterate over markdown files in the directory
    for filename in sorted(os.listdir(md_dir)):
        if filename.endswith(".md"):
            try:
                md_path = os.path.join(md_dir, filename)
                chunk_path = os.path.join(
                    chunk_dir, f"{filename[:-3]}.json")  # JSON output path

                # Skip processing if JSON file already exists
                if os.path.exists(chunk_path):
                    print(f"Skipping {filename} (already processed).")
                    continue

                # Read the markdown file
                with open(md_path, "r", encoding="utf-8") as f:
                    md_content = f.read()

                # Process the markdown content
                chunks = process_md_file(md_content)

                # Save chunks as JSON
                with open(chunk_path, "w", encoding="utf-8") as f:
                    json.dump(chunks, f, indent=2)

                print(f"Processed {filename} -> Saved {chunk_path}")
            except:
                print(
                    f"Error in processing {filename}, skipping this for now.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process markdown files in a directory.")
    parser.add_argument(
        "md_dir", type=str, help="Path to the directory containing markdown files.")
    args = parser.parse_args()
    process_md_directory(args.md_dir)
