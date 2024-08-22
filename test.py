from scrape_page import extract_content
import time

PATH = 'json_data/'
url_head = 'https://minecraft.wiki/w/'

# read in all lines in urls.txt
with open('urls.txt', 'r') as f:
    urls = f.readlines()
    # remove whitespace characters like `\n` at the end of each line
    urls = [x.strip() for x in urls]

for url in urls:
    print('Scraping ' + url)
    extract_content(url, PATH + url[len(url_head):] + '.json')
    time.sleep(5)
