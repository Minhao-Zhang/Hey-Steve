from tqdm import tqdm
import argparse
import re
import html2text

UNWANTED_HEADING_2 = ['Achievements', 'Advancements', 'Contents', 'Data values',
                      'Entities', 'External links', 'Gallery', 'History', 'Issues',
                      'Navigation', 'Navigation menu', 'References', 'Sounds',
                      'Trivia', 'Video', 'Videos', 'See also']


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

        markdown_content = h.handle(html_content)

        # delete "[edit | edit source]"
        markdown_content = markdown_content.replace("[edit | edit source]", "")

        return markdown_content
    except Exception as e:
        return f"Error: Could not convert HTML to markdown. {e}"


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


def replace_weird_code(markdown_content: str) -> str:
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
        md_content = convert_html_to_markdown(f"downloads/{name}.html")
        md_content = remove_unwanted_heading_2(md_content)
        md_content = remove_json_blocks(md_content)
        md_content = remove_junk_content(md_content)
        md_content = replace_weird_code(md_content)

        with open(f"data/downloads/{name}.md", "w") as f:
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
