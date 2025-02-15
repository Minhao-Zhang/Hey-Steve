import re


def split_markdown_sections(text):
    """
    Splits a Markdown document into:
    1. Title (Markdown H1 heading)
    2. Disambiguation Section (text before the repeated heading)
    3. Table Section (from repeated heading until two blank lines)
    4. description Section (everything after two blank lines, stopping before a level 2 heading)

    Returns:
        tuple (title, disambiguation, table, description)
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

    return title, disambiguation, table_text, description
