# MC AI Assistant

A Minecraft Assistant that provides information about mobs, blocks, items, and more using LLM powered RAG. 

Minecraft wiki is scraped as knowledge base. 
Then, Langchain is used to dynamically chunk the data into paragraphs. 
Contextual Retrieval is used to assist RAG in finding the most relevant information.
Special embed models are used to ensure accuracy and efficiency 
ChromaDB is used to store vector data for the RAG. 
Provided endpoint for any model you wish to use for the RAG. 

## Run this yourself 

1. Clone the repository
```bash
git clone git@github.com:Minhao-Zhang/MC-AI-Assistant.git
```
2. Install the requirements
```bash 
conda create -n mc-assistance python=3.12.8
```
3. Download all the pages as into `downloads`. 
    
    As far as I understand, the content on [minecraft.wiki](https://minecraft.wiki) are licensed under [cc by-nc-sa 3.0](https://creativecommons.org/licenses/by-nc-sa/3.0/deed.en). Thus, I will not include them in here. 

    I provided several files in the `urls` folder. They are all page names as they all share a common prefix of `https://minecraft.wiki/w/`. Thus, I would dynamically pad the URLs with the prefix.
    
    1. You can directly use `sh download.sh PATH_TO_URL_FILE` or `.\Download-Webpages.ps1 PATH_TO_URL_FILE` to download all the pages. You can see them under `downloads`. 
    2. You can alternatively update the URLs as mine might be outdated. You can run `python get_page_names.py` to get the latest URLs. 

    These URL files are very important as they allow us to process each types of page differently. Currently, I am only considering `mobs`, `blocks`, and `items` in Java version of Minecraft. 

4. Run the `python html_to_markdown.py PATH_TO_URL_FILE` to process the pages into a semi-refined markdown file. In the process, only the most basic information is kept. 