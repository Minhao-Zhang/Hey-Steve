import os
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownTextSplitter
from chroma_embed import *
from sentence_transformers import SentenceTransformer

st = SentenceTransformer("all-MiniLM-L6-v2", device="cuda")


def custom_embed(x):
    return st.encode(x, convert_to_numpy=True)


rcts = RecursiveCharacterTextSplitter(
    chunk_size=600,
    chunk_overlap=200,
    separators=["\n\n", "\n", ".", "?", "!", " ", ""],
    keep_separator=False
)
rtc = RecursiveTokenChunker(
    chunk_size=200,
    chunk_overlap=50,
    separators=["\n\n", "\n", ".", "?", "!", " ", ""],
    keep_separator=False
)
ftc = FixedTokenChunker(
    chunk_size=250,
    chunk_overlap=50
)
csc = ClusterSemanticChunker(
    embedding_function=custom_embed,
    max_chunk_size=200,
    min_chunk_size=50
)


input_dir = "data/md"
rcts_dir = "data/chunks_rcts"
rtc_dir = "data/chunks_rtc"
ftc_dir = "data/chunks_ftc"
csc_dir = "data/chunks_csc"

if not os.path.exists(rcts_dir):
    os.makedirs(rcts_dir)

if not os.path.exists(rtc_dir):
    os.makedirs(rtc_dir)

if not os.path.exists(ftc_dir):
    os.makedirs(ftc_dir)

if not os.path.exists(csc_dir):
    os.makedirs(csc_dir)

for filename in os.listdir(input_dir):
    if filename.endswith(".md"):
        filepath = os.path.join(input_dir, filename)
        with open(filepath, "r") as f:
            text = f.read()
        chunks = rcts.split_text(text)
        output_filepath = os.path.join(
            rcts_dir, filename.replace(".md", ".json"))
        with open(output_filepath, "w") as outfile:
            json.dump(chunks, outfile, indent=4)

for filename in os.listdir(input_dir):
    if filename.endswith(".md"):
        filepath = os.path.join(input_dir, filename)
        with open(filepath, "r") as f:
            text = f.read()
        chunks = rtc.split_text(text)
        output_filepath = os.path.join(
            rtc_dir, filename.replace(".md", ".json"))
        with open(output_filepath, "w") as outfile:
            json.dump(chunks, outfile, indent=4)

for filename in os.listdir(input_dir):
    if filename.endswith(".md"):
        filepath = os.path.join(input_dir, filename)
        with open(filepath, "r") as f:
            text = f.read()
        chunks = ftc.split_text(text)
        output_filepath = os.path.join(
            ftc_dir, filename.replace(".md", ".json"))
        with open(output_filepath, "w") as outfile:
            json.dump(chunks, outfile, indent=4)

# for filename in os.listdir(input_dir):
#     if filename.endswith(".md"):
#         filepath = os.path.join(input_dir, filename)
#         with open(filepath, "r") as f:
#             text = f.read()
#         chunks = csc.split_text(text)
#         output_filepath = os.path.join(
#             csc_dir, filename.replace(".md", ".json"))
#         with open(output_filepath, "w") as outfile:
#             json.dump(chunks, outfile, indent=4)
