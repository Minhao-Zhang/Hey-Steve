# MC-Assistant

A Minecraft Assistant that provides information about mobs, blocks, items, and more using LLM powered RAG. 

## Run this yourself 

Clone this repository then install the required packages.
```bash
conda create -n mc-assistant python=3.11.9
pip install -r requirements.txt
```

Pull some LLMs from Ollama. 
This is dependent on the LLMs you want to use and how much computing power you have available. 
Here, I will use the llama3.2 model families. 
```bash
ollama pull llama3.2 
```

Create data and cache directory. 
```bash
mkdir data cache 
```

Scrape data from Minecraft wiki. 
This is done in [scrape.ipynb](scrape.ipynb) since un unknown bug would occur if it is run in a python script. 
You will be banned for a while if you scrape too much data. 
That is why a cache system is implemented. 

