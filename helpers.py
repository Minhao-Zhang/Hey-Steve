import re
from typing import List
import requests
import html2text
import warnings
import ollama
from langchain_text_splitters import MarkdownHeaderTextSplitter
from tqdm import tqdm

LONG_CONTEXT_MODEL = '48k-llama3.2:1b'
GENERAL_MODEL = 'llama3.2'


def html2md(html: str) -> str:
    """Custom function to convert HTML to Markdown

    Args:
        html (str): HTML content

    Returns:
        str: Markdown content
    """
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    h.ignore_emphasis = True
    h.skip_internal_links = True
    h.unicode_snob = True
    h.bypass_tables = False
    h.ignore_tables = False
    h.body_width = 0  # No wrapping
    return h.handle(html)


def write_to_file(file_path: str, data: str) -> None:
    """
    Write data to a file

    Args:
        file_path (str): path to the file
        data (str): data to write to the file
    """
    with open(file_path, 'w') as file:
        file.write(data)


def remove_edit_source(text: str) -> str:
    """
    Remove '[edit | edit source]' from text

    Args:
        text (str): markdown style text

    Returns:
        str: text with '[edit | edit source]' removed
    """
    return re.sub(r'\[edit \| edit source\]', '', text)


def remove_unnecessary_sections(text: str) -> str:
    """
    Remove some unnecessary sections from the text. 
    See source for the list of sections to remove.

    Args:
        text (str): markdown style text

    Returns:
        str: text without not unnecessary sections from the text
    """

    UNWANTED_HEADING_2 = ['Achievements', 'Advancements', 'Contents', 'Data values', 'Entities', 'External links',
                          'Gallery', 'History', 'Issues', 'Navigation', 'Navigation menu', 'References', 'Sounds', 'Trivia', 'Video', '|', 'Videos', 'See also']

    text_line = text.split('\n')
    new_text = []

    to_remove = False  # Flag to remove the section
    for line in text_line:
        if line.startswith('## '):
            heading = line[3:].strip()
            if heading in UNWANTED_HEADING_2:
                to_remove = True
            else:
                to_remove = False
                new_text.append(line)
        else:
            if not to_remove:
                new_text.append(line)

    return '\n'.join(new_text)


def scrape_normal(url: str, cache=True) -> str:
    """
    Scrape the content of a normal page

    Args:
        url (str): URL of the page

    Returns:
        str: Markdown content
    """

    URL_HEAD = 'https://minecraft.wiki/w/'

    # Get the HTML content
    if cache:
        # Use cache
        file_path = f'cache/{url[len(URL_HEAD):]}.html'
        try:
            print(f'Reading cache file for {url}')
            with open(file_path, 'r') as file:
                html = file.read()
        except FileNotFoundError:
            warnings.warn(
                f'Cache file not found for {url}. Scraping the page.')
            response = requests.get(url)
            html = response.text
            with open(file_path, 'w') as file:
                file.write(html)
    else:
        response = requests.get(url)
        html = response.text
        with open(f'cache/{url[len(URL_HEAD):]}.html', 'w') as file:
            file.write(html)

    md = html2md(html)
    md = remove_edit_source(md)
    md = remove_unnecessary_sections(md)

    return md


def scrape_mob(url: str, cache=True):
    """
    Scrape the content of a mob page

    Args:
        url (str): URL of the page

    Returns:
        str: Markdown content
    """
    text = scrape_normal(url, cache)

    # find the first level 2 heading
    title_last = text.index('##')
    text_pre = text[:title_last]
    text_pre = text_pre.split('\n')

    # remove disambiguate content
    title = text_pre[0][2:]
    text_pre = text_pre[text_pre.index(title) + 1:]
    text_pre.insert(0, "# " + title)

    # between the first ## Spawning heading
    # there's a json object that we need to remove
    json_start = text_pre.index('    {')
    json_end = text_pre.index('    }')
    text_pre = text_pre[:json_start] + text_pre[json_end + 1:]

    text_pre = '\n'.join(text_pre)

    return text_pre + '\n' + text[title_last:]


def parse_mob_info_table(text: str) -> str:
    """
    Extra processing for the ill-formed mob info table

    Args:
        text (str): Markdown content for mob page

    Returns:
        str: Markdown content with mob info table processed
    """

    # remove anything before "Health points" but the title
    title = text[:text.index('\n')]
    text = text[text.index('Health points'):]
    # the health points will have a form of number x number
    # we need to remove the second number
    try:
        linebreak_index = text.index('\n')
        health_str = re.sub(r"× \d+(\.\d+)?( |$)", "", text[:linebreak_index])
        text = health_str + text[linebreak_index:]
    except ValueError:
        pass
    split_index = text.index('## ')
    text_pre = text[:split_index]
    text_post = text[split_index:]

    text_pre = text_pre.split('\n')
    text_pre_keep = text_pre[-4:-3]

    table = text_pre[:-4]

    table_content = "\n".join(table)

    messages = [
        {'role': 'system',
            'content': f'You are editing mob content for the Minecraft wiki. The following is an ill-formatted markdown table that describes information about the mob {title[2:]}. The table can have many rows but only two columns. Please summarize the table content and write them in bullet form. Respond only with the required information and nothing else .'},
        {'role': 'user', 'content': table_content}
    ]

    response = ollama.chat(model=GENERAL_MODEL, messages=messages)
    formatted_table_content = response['message']['content']

    return title + '\n\n' + "\n".join(text_pre_keep) + '\n\n' + formatted_table_content + '\n\n' + text_post


def chunk_and_contextualize_text(text: str) -> List[str]:
    """
    Chunk the text into smaller parts and add some context to the text

    Args:
        text (str): Markdown content

    Returns:
        List[str]: Contextualized and chunked text based on markdown headers
    """

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on)
    text_chunks = splitter.split_text(text)

    text_chunks_contextual = []

    for chunk in tqdm(text_chunks, desc="Processing chunks"):
        chunk_text = chunk.page_content

        msg = f"""
        <document> 
        {text} 
        </document> 
        Here is the chunk we want to situate within the Minecraft wiki document
        <chunk> 
        {chunk_text}
        </chunk> 
        Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else. 
        """
        messages = [{'role': 'user', 'content': msg}]
        response = ollama.chat(model=LONG_CONTEXT_MODEL, messages=messages)
        text_chunks_contextual.append(
            response['message']['content'] + chunk_text)

    return text_chunks_contextual


def extract_items():
    """
    Extract all the items from the Minecraft wiki and write them to a file.
    """

    url = "https://minecraft.wiki/w/Item"

    # try to get the content from the cache
    try:
        with open('cache/Item.html', 'r') as f:
            item = f.read()
    except:
        response = requests.get(url)
        item = response.text

    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.ignore_emphasis = True
    h.skip_internal_links = True
    h.unicode_snob = True
    h.body_width = 0
    md = h.handle(item)

    start = md.index('## List of items')
    end = md.index('## Unimplemented items')

    list_of_items_md = md[start:end]

    matches = re.findall(r"/w/([^ ]+) ", list_of_items_md)
    items = set(matches)
    items = sorted(list(items))
    items = '\n'.join(items)

    write_to_file('urls/items.txt', items)


def extract_blocks():
    """
    Extract all the blocks from the Minecraft wiki and write them to a file.
    """

    url = "https://minecraft.wiki/w/Block"

    # try to get the content from the cache
    try:
        with open('cache/Block.html', 'r') as f:
            item = f.read()
    except:
        response = requests.get(url)
        item = response.text

    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.ignore_emphasis = True
    h.skip_internal_links = True
    h.unicode_snob = True
    h.body_width = 0
    md = h.handle(item)

    start = md.index('## List of blocks')
    end = md.index('### Technical blocks')

    list_of_blocks_md = md[start:end]

    matches = re.findall(r"/w/([^ ]+) ", list_of_blocks_md)
    blocks = set(matches)
    blocks = sorted(list(blocks))
    # remove all the image files
    blocks = [block for block in blocks if block[:5] != 'File:']
    # remove the disambiguation tag
    blocks = [re.sub(r'_\\\(block\\\)', '', block) for block in blocks]
    blocks = '\n'.join(blocks)

    write_to_file('urls/blocks.txt', blocks)
