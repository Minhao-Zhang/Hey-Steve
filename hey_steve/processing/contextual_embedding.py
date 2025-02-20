from hey_steve.LLMs import LLMClient


def get_context_for_chunk(llm_client: LLMClient, md_context: str, chunk: str, prompt_template: str = "./hey_steve/prompt_template/contexual_chunk.txt"):
    """
    Gets the context for a chunk of text using a language model.

    Args:
        llm_client (LLMClient): LLMClient object for language model interaction.
        md_context (str): Contextual information in Markdown format.
        chunk (str): The chunk of text to embed.
        prompt_template (str): Path to the prompt template file.

    Returns:
        str: The language model's response.
    """
    with open(prompt_template, 'r') as f:
        pt = f.read()
    user_prompt = pt.format(WHOLE_DOCUMENT=md_context, CHUNK_CONTENT=chunk)
    response = llm_client.chat(user_prompt)
    return response
