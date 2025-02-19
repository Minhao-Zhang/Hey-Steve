from mc_ai_assistant.data_processing.extract_heading_info import *
from mc_ai_assistant.data_processing.chunk_markdown import chunk_markdown, semantic_chunks
from mc_ai_assistant.data_processing.contextual_embedding import get_context_for_chunk
from mc_ai_assistant.utils import *
from mc_ai_assistant.rag_service.rag import *
import os
import json

llm_client = SiliconFlowClient()
rag = MC_RAG()


def get_raw_md_filenames():
    """Get list of filenames in the raw_md directory.

    Returns:
        list: List of filenames in the raw_md directory
    """
    raw_md_path = "raw_md"
    if not os.path.exists(raw_md_path):
        return []

    return [f for f in os.listdir(raw_md_path)
            if os.path.isfile(os.path.join(raw_md_path, f))]


filenames = get_raw_md_filenames()
filenames = sorted(filenames)

for fn in filenames:
    print(f"Processing file: {fn}")
    with open(f"raw_md/{fn}", 'r') as f:
        md_content = f.read()
        title, disambiguation, table_text, description, rest = extract_sections(
            md_content)

        table_json_string = extract_table(table_text, llm_client)
        table_md = parse_json_to_markdown(table_json_string)
        md_content = title + "\n" + disambiguation + "\n" + table_md + "\n" + rest

        chunks = chunk_markdown(md_content)
        chunks = [c.page_content for c in chunks]
        chunks = semantic_chunks(chunks)

        contextual_chunks = []
        for chunk in chunks:
            context = get_context_for_chunk(llm_client, md_content, chunk)
            contextual_chunks.append(f"{context}\n{chunk}")

        # Add contextualized chunks to MC_RAG
        documents = [{"text": chunk} for chunk in contextual_chunks]
        rag.add_documents(documents)

        with open(os.path.join("data", f"{fn[:-3]}.json"), 'w') as outfile:
            json.dump(contextual_chunks, outfile, indent=4)
