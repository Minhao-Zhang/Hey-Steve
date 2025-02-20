import re
import json
from hey_steve.LLMs import LLMClient


def extract_sections(text):
    """
    Splits a Markdown document into:
    1. Title (Markdown H1 heading)
    2. Disambiguation Section (text before the repeated heading)
    3. Table Section (from repeated heading until two blank lines)
    4. description Section (everything after two blank lines, stopping before a level 2 heading)

    Returns:
        tuple (title, disambiguation, table, description, remaining_text)
    """

    # Step 1: Extract the Title
    lines = text.strip().splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError("First line must be a Markdown Level 1 heading")

    title = lines[0].strip()  # First line is always the title
    # Extract heading text, ignoring case
    heading_value = title[2:].strip().lower()

    # Step 2: Extract Disambiguation Section (everything until the heading reappears)
    disambiguation_lines = []
    i = 1  # Start after the title
    while i < len(lines) and lines[i].strip().lower() != heading_value:
        disambiguation_lines.append(lines[i])
        i += 1
    disambiguation = "\n".join(disambiguation_lines).strip()

    # Step 3: Extract Table Section (everything after heading until two blank lines)
    table_lines = []
    i += 1  # Move past the heading
    blank_count = 0
    while i < len(lines):
        if re.match(r"^\s*$", lines[i]):  # Count blank lines
            blank_count += 1
        else:
            blank_count = 0  # Reset if non-blank line appears

        table_lines.append(lines[i])
        i += 1

        if blank_count >= 2:  # Stop after two consecutive blank lines
            break

    table_text = "\n".join(table_lines).strip()

    # Step 4: Extract description Section (everything after two blank lines, stopping before a level 2 heading)
    # Skip remaining blank lines
    while i < len(lines) and re.match(r"^\s*$", lines[i]):
        i += 1

    description_lines = []
    while i < len(lines):
        if lines[i].startswith("## "):  # Stop at the first level 2 heading
            break
        description_lines.append(lines[i])
        i += 1
    description = "\n".join(description_lines).strip()

    remaining_text = "\n".join(lines[i:]).strip()

    return title, disambiguation, table_text, description, remaining_text


def extract_table(table_text: str, llm_client: LLMClient, prompt_template: str = "./hey_steve/prompt_template/extract_table.txt"):
    """
    Extracts a table from the table_text, which is a Markdown-formatted table.

    Args:
        table_text (str): Markdown-formatted table
        llm_client (LLMClient): LLMClient object to use for language model queries

    Returns:
        list: List of dictionaries, where each dictionary represents a row in the table
    """
    with open(prompt_template, 'r') as f:
        pt = f.read()

    user_prompt = pt + table_text
    response = llm_client.chat(user_prompt)
    # Extract content from markdown code block
    code_block_match = re.search(
        r'```(?:json)?\n(.*?)\n```', response, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1)
    return response  # Fallback if no code block found


def parse_json_to_markdown(json_str: str) -> str:
    """
    Parses a JSON string containing a list of key-value pairs into markdown format.

    Args:
        json_str (str): JSON string containing a list of key-value pairs

    Returns:
        str: Markdown formatted string
    """
    try:
        data = json.loads(json_str)
        if not isinstance(data, dict):
            raise ValueError("Input JSON must be an object")

        markdown_lines = []
        for key, value in data.items():
            markdown_lines.append(f"- **{key}**: {value}")
        return "\n".join(markdown_lines)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {str(e)}")
