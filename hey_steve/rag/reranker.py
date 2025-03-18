import torch
from sentence_transformers import CrossEncoder


class Reranker:
    def __init__(self, model_name='BAAI/bge-reranker-v2-m3'):
        self.model = CrossEncoder(
            model_name,
            automodel_args={"torch_dtype": "auto"},
        )

    def calculate_scores(self, pairs: list[list[str]]) -> torch.Tensor:
        scores = self.model.predict(pairs)
        return scores

    def rerank(self, query_text: str, search_results: list[str]) -> list[str]:
        """Reranks search results based on the reranker score.

        Args:
            query_text: The query text.
            search_results: The list of search results to rerank.

        Returns:
            The reranked list of search results.
        """

        pairs = [[query_text, doc['text']] for doc in search_results]
        scores = self.calculate_scores(pairs)
        reranked_results = sorted(
            zip(search_results, scores.tolist()), key=lambda x: x[1], reverse=True)

        return [result[0] for result in reranked_results]


if __name__ == '__main__':
    # Example usage
    reranker = Reranker()
    pairs = [['what is panda?', 'hi'],
             ['what is panda?', 'The giant panda (Ailuropoda melanoleuca), sometimes called apanda bear or simply panda, is a bear species endemic to China.']]
    scores = reranker.calculate_scores(pairs)
    print(scores)
