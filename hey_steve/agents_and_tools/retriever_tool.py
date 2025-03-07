from smolagents import Tool
from hey_steve.rag import SteveRAG


class RetrieverTool(Tool):
    name = "mc_knowledge_base"
    description = (
        "Uses semantic search to retrieve the parts of documentation that could be most relevant to answer your query about Minecraft."
    )
    inputs = {
        "query": {
            "type": "string",
            "description": "The query to perform. This should be semantically close to your target documents. Use the affirmative form rather than a question.",
        },
        "n_result": {
            "type": "integer",
            "description": "The positive integer number of document chunks to retrieve. Defaults to 5.",
            "nullable": True
        }
    }
    output_type = "string"

    def __init__(self, steve_rag: SteveRAG, **kwargs):
        super().__init__(**kwargs)
        self.steve_rag = steve_rag

    def forward(self, query: str, n_result: str = 5) -> str:
        assert isinstance(query, str), "Your search query must be a string"
        assert isinstance(n_result, int), "n_result must be an integer"
        assert n_result > 0, "n_reuslt must be a positive integer"

        docs = self.steve_rag.query_with_reranking(query, n_results=n_result)
        return "\nRetrieved documents:\n" + "".join(
            [f"\n\n===== Document {str(i)} =====\n" +
             doc['text'] for i, doc in enumerate(docs)]
        )
