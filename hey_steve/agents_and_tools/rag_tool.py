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
        }
    }
    output_type = "string"

    def __init__(self, steve_rag: SteveRAG, **kwargs):
        super().__init__(**kwargs)
        self.steve_rag = steve_rag

    def forward(self, query: str) -> str:
        assert isinstance(query, str), "Your search query must be a string"
        docs = self.steve_rag.query(query, n_results=5)
        return "\nRetrieved documents:\n" + "".join(
            [f"\n\n===== Document {str(i)} =====\n" +
             doc['text'] for i, doc in enumerate(docs)]
        )
