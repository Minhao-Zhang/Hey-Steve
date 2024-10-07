import re
import requests
import html2text
import warnings


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


def remove_code(text: str) -> str:
    """
    Remove code from text

    Args:
        text (str): markdown style text

    Returns:
        str: text with code removed
    """
    return re.sub(r'`[^`]+`', '', text)


def remove_unnecessary_sections(text: str) -> str:
    """
    Remove some unnecessary sections from the text. These sections are 
     ['Achievements', 'Advancements', 'Contents', 'Data values', 
     'Entities', 'External links', 'Gallery', 'History', 'Issues', 
     'Navigation', 'Navigation menu', 'References', 'Sounds', 
     'Trivia', 'Video', '|']

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

    # Convert HTML to Markdown
    md = html2md(html)

    # Remove '[edit | edit source]' from the Markdown content
    md = remove_edit_source(md)

    # Remove code from the Markdown content
    md = remove_code(md)

    # Remove some unnecessary sections from the Markdown content
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

    text = text.split('## Spawning')

    text_pre = text[0].split('\n')

    # remove disambiguate content
    title = text_pre[0][2:]
    text_pre = text_pre[text_pre.index(title) + 1:]
    text_pre.insert(0, "# " + title)

    # between the first ## Spawning heading
    # there's a json object that we need to remove
    text_pre = text_pre[:text_pre.index('    {')]
    text_pre = "\n".join(text_pre)

    return text_pre + '\n## Spawning' + text[1]
