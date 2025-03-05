from bs4 import BeautifulSoup
from tqdm import tqdm
import argparse
import re
import html2text

# UNWANTED_HEADING_2 = ['Achievements', 'Advancements', 'Contents', 'Data values',
#                       'Entities', 'External links', 'Gallery', 'History', 'Issues',
#                       'Navigation', 'Navigation menu', 'References', 'Sounds',
#                       'Trivia', 'Video', 'Videos', 'See also']
UNWANTED_HEADING_2 = ['Contents', 'Data values', 'External links', 'Gallery',
                      'Issues', 'Navigation', 'Navigation menu', 'References',
                      'Sounds', 'Video', 'Videos', 'See also']


def convert_html_to_markdown(html_file):
    """
    Converts an HTML file to markdown using html2text.
    """
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        return f"Error: File '{html_file}' not found."
    except Exception as e:
        return f"Error: Could not read file '{html_file}'. {e}"

    try:
        h = html2text.HTML2Text()

        h.ignore_links = True
        h.ignore_mailto_links = True
        h.ignore_emphasis = True
        h.ignore_images = True
        h.escape_all = True
        h.bypass_tables = True

        markdown_content = h.handle(html_content)

        # delete "[edit | edit source]"
        markdown_content = markdown_content.replace("[edit | edit source]", "")

        return markdown_content
    except Exception as e:
        return f"Error: Could not convert HTML to markdown. {e}"


def html_table_to_markdown(html: str) -> str:
    """
    Convert an HTML table to markdown format. If there are lists inside the table cells,
    it will convert them into a single line, separated by semicolons.

    Args:
        html (str): The HTML table code as a string.

    Returns:
        str: The markdown formatted table.
    """
    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Find the table element
    table = soup.find('table')

    if not table:
        return ""

    rows = table.find_all('tr')
    markdown_table = []

    # Function to handle complex cell content (like lists)
    def process_cell_content(cell):
        # If the cell contains <ul> or <ol> (unordered or ordered lists), process the list items
        if cell.find(['ul', 'ol']):
            items = []
            for li in cell.find_all('li'):
                items.append(li.get_text(strip=True))
            return ' '.join([f"* {item}" for item in items])

        # Otherwise, return the text content, stripping extra whitespace and ignoring line breaks
        return cell.get_text(strip=True).replace('\n', ' ').replace('\r', ' ')

    # Loop through each row in the table
    for row in rows:
        # Find all td or th elements in the row
        cells = row.find_all(['td', 'th'])
        # Process each cell's content
        cell_text = [process_cell_content(cell) for cell in cells]
        markdown_table.append(cell_text)

    # Create the markdown table string
    if not markdown_table:
        return ""

    # Convert each row into markdown format
    markdown_lines = []
    for row in markdown_table:
        markdown_lines.append("| " + " | ".join(row) + " |")

    # Add separator line (only if the table has more than one row)
    if len(markdown_lines) > 1:
        separator = "|" + " | ".join(['---' for _ in markdown_table[0]]) + "|"
        markdown_lines.insert(1, separator)

    return "\n".join(markdown_lines)


def parse_html_tables(markdown_content):
    while "<table>" in markdown_content:
        start = markdown_content.index("<table>")
        end = markdown_content.index("</table>")
        # Add a check to ensure that start and end indices are valid
        if start >= end:
            break
        table_text = markdown_content[start: end + len("</table>")]
        md_table_text = html_table_to_markdown(table_text)
        # md_table_text = describe_table(md_table_text)
        markdown_content = markdown_content[:start] + \
            md_table_text + markdown_content[end + len("</table>"):]

    return markdown_content


# def describe_table(markdown_content):
#     llm_client = OllamaClient()
#     with open("hey_steve/prompt_template/table_to_text.txt", "r") as f:
#         pt = f.read()

#     user_message = pt.format(md_table=markdown_content)
#     return llm_client.chat(user_message=user_message)


def remove_unwanted_heading_2(markdown_content):
    """
    Removes unwanted heading 2 sections from a markdown string using regex.
    """
    unwanted_headings = '|'.join(re.escape(heading)
                                 for heading in UNWANTED_HEADING_2)
    pattern = r'##\s+(' + unwanted_headings + r')\s*\n(.*?)(?=(?:\n##\s)|$)'
    markdown_content = re.sub(pattern, '', markdown_content, flags=re.DOTALL)
    return markdown_content


def remove_json_blocks(markdown_content: str) -> str:
    """
    Remove JSON-like blocks from the markdown content.

    This function assumes that any block starting with a line that (after stripping)
    begins with "{" and continuing until the braces are balanced is unwanted.
    """
    lines = markdown_content.splitlines(keepends=True)
    result = []
    in_json_block = False
    brace_count = 0

    for line in lines:
        # If we're not already inside a JSON block, check if the line starts one.
        if not in_json_block:
            if line.lstrip().startswith('{'):
                in_json_block = True
                brace_count = line.count('{') - line.count('}')
                # Skip this line.
                continue
            else:
                result.append(line)
        else:
            # We're inside a JSON block, update the brace count.
            brace_count += line.count('{') - line.count('}')
            # If we've balanced all the braces, end the JSON block.
            if brace_count <= 0:
                in_json_block = False
            # Skip all lines inside the JSON block.
            continue

    return ''.join(result)


def remove_junk_content(markdown_content: str) -> str:
    """
    Remove the junk line 'Jump to navigation Jump to search' if present early in the content.
    """
    lines = markdown_content.splitlines()
    try:
        # Find its position
        index = lines.index("Jump to navigation Jump to search")
        del lines[index]  # Remove it
    except ValueError:
        pass  # Do nothing if the line is not found
    return "\n".join(lines)


def replace_weird_unicode(markdown_content: str) -> str:
    replace_table = {
        "×": "x",
        chr(8204): ""
    }

    for key, value in replace_table.items():
        markdown_content = markdown_content.replace(key, value)

    return markdown_content


def main(url_file):
    with open(url_file, "r") as f:
        names = f.readlines()
    names = [name.strip() for name in names]

    # Process the name a bit
    names = [name.replace("'", "_") for name in names]
    names = [name.replace("(", "_").replace(")", "_") for name in names]

    for name in tqdm(names, desc="Converting HTML to Markdown"):
        md_content = convert_html_to_markdown(f"data/downloads/{name}.html")
        md_content = parse_html_tables(md_content)
        md_content = remove_unwanted_heading_2(md_content)
        md_content = remove_json_blocks(md_content)
        md_content = remove_junk_content(md_content)
        md_content = replace_weird_unicode(md_content)

        with open(f"data/md/{name}.md", "w") as f:
            f.write(md_content)


if __name__ == "__main__":
    # parser = argparse.ArgumentParser(
    #     description='Convert HTML files to Markdown.')
    # parser.add_argument('url_file', type=str,
    #                     help='Path to the file containing URLs.')
    # args = parser.parse_args()

    # main(args.url_file)

    main("urls/mobs.txt")
    main("urls/items.txt")
    main("urls/blocks.txt")
