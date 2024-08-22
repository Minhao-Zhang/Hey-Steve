from bs4 import BeautifulSoup
import requests
import re
import json


def parse_general(url, file_name):
    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    # Define the heading tags to look for
    heading_tags = ['h1', 'h2', 'h3', 'h4']

    # Initialize the content tree and a stack to keep track of current levels
    content_tree = {}
    current_stack = [{'level': 0, 'content': content_tree}]

    # Function to find the current parent content based on level
    def find_parent(level):
        while current_stack and current_stack[-1]['level'] >= level:
            current_stack.pop()
        return current_stack[-1]['content']

    # Function to parse table and convert it to a list of formatted strings
    def parse_table(table):
        headers = [clean_text(th.get_text(strip=True).replace('\n', ' '))
                   for th in table.find_all('th')]
        rows = []
        for row in table.find_all('tr')[1:]:  # Skip header row
            cells = row.find_all('td')
            if len(cells) == len(headers):
                row_data = ', '.join([f"{headers[i]} is {clean_text(cells[i].get_text(
                    strip=True).replace('\n', ' '))}" for i in range(len(cells))])
                rows.append(row_data)
        return rows

    # Function to extract and format code content, adding spaces around <a> tags
    def extract_code_content(element):
        if element.name == 'code':
            text_parts = []
            for child in element.contents:
                if child.name == 'a':
                    text_parts.append(
                        f' {clean_text(child.get_text(strip=True).replace("\n", " "))} ')
                elif hasattr(child, 'get_text'):
                    text_parts.append(clean_text(
                        child.get_text(strip=True).replace('\n', ' ')))
                else:
                    text_parts.append(clean_text(str(child)))

            text = ''.join(text_parts).strip()
            return f'`{text}`'
        return clean_text(element.get_text(strip=True).replace('\n', ' '))

    # Function to clean and remove specific Unicode characters from the text
    def clean_text(text):
        # Remove specific Unicode characters
        return re.sub(r'[\u200c]', '', text)

    # Function to process elements and update the content tree
    def process_element(element):
        if hasattr(element, 'name'):
            if element.name in heading_tags:
                level = int(element.name[1])
                heading_text = clean_text(element.get_text(strip=True))

                # Remove '[edit|edit source]' from heading text using regex
                heading_text = re.sub(
                    r'\s*\[\s*edit\s*\|\s*edit\s*source\s*\]', '', heading_text)

                parent_content = find_parent(level)
                parent_content[heading_text] = {}
                current_stack.append(
                    {'level': level, 'content': parent_content[heading_text]})
            elif element.name == 'p':
                parent_content = current_stack[-1]['content']
                content_text = clean_text(
                    element.get_text(strip=False).replace('\n', ' '))
                if '_content' not in parent_content:
                    parent_content['_content'] = []
                parent_content['_content'].append(content_text)
            elif element.name == 'table':
                parent_content = current_stack[-1]['content']
                table_data = parse_table(element)
                if '_content' not in parent_content:
                    parent_content['_content'] = []
                # Add table rows directly to _content
                parent_content['_content'].extend(table_data)
                element['parsed'] = True  # Mark the element as parsed
            elif element.name == 'code':
                parent_content = current_stack[-1]['content']
                code_content = extract_code_content(element)
                if '_content' not in parent_content:
                    parent_content['_content'] = []
                parent_content['_content'].append(code_content)
                element['parsed'] = True  # Mark the element as parsed

    # Use BFS to process each element
    queue = [soup.body]
    while queue:
        element = queue.pop(0)
        # Check if the element has already been parsed
        if hasattr(element, 'name') and not element.get('parsed'):
            process_element(element)
            # Add children to the queue
            queue.extend(element.find_all(recursive=False))

    # Return only the inner content of the outermost layer
    if content_tree:
        json_data = json.dumps(next(iter(content_tree.values())), indent=2)
    else:
        json_data = json.dumps({}, indent=2)

    def remove_keys(json_data):
        removing_keys = {'Fan Feed', 'Achievements', 'History', 'Issues',
                         'Trivia', 'Gallery', 'See also', 'References',
                         'Contents', 'Navigation', 'Sounds'}

        if isinstance(json_data, dict):
            # Create a new dictionary excluding keys in removing_keys
            new_data = {}
            for k, v in json_data.items():
                if k not in removing_keys:
                    new_data[k] = remove_keys(v)
            return new_data
        elif isinstance(json_data, list):
            # Process each item in the list
            return [remove_keys(item) for item in json_data]
        else:
            # Return the data as is if it's neither a dictionary nor a list
            return json_data

    # Suppose 'json_data' is your JSON data as a Python dictionary
    json_data = remove_keys(json.loads(json_data))

    with open(file_name, 'w') as f:
        json.dump(json_data, f, indent=2)
