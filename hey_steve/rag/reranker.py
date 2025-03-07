import time
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class Reranker:
    def __init__(self, model_name='BAAI/bge-reranker-v2-m3'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name)
        self.model.eval()

    def calculate_scores(self, pairs: list[list[str]]) -> torch.Tensor:
        start = time.time()
        with torch.no_grad():
            inputs = self.tokenizer(pairs, padding=True, truncation=True,
                                    return_tensors='pt', max_length=512)
            scores = self.model(
                **inputs, return_dict=True).logits.view(-1, ).float()
            print(time.time() - start)
            return scores

    def rerank(self, query_text: str, search_results: list[str]) -> list[str]:
        """Reranks search results based on the reranker score.

        Args:
            query_text: The query text.
            search_results: The list of search results to rerank.

        Returns:
            The reranked list of search results.
        """

        with open("temp.txt", "a") as f:
            f.write("Query: " + query_text + "\n\n")
            for doc in search_results:
                f.write(doc['text'] + "\n")
                f.write("="*80 + "\n")

        pairs = [[query_text, doc['text']] for doc in search_results]
        scores = self.calculate_scores(pairs)
        reranked_results = sorted(
            zip(search_results, scores.tolist()), key=lambda x: x[1], reverse=True)

        with open("temp.txt", "a") as f:
            f.write("\n\nAfter Rerank\n\n")
            for doc in search_results:
                f.write(doc['text'] + "\n")
                f.write("="*80 + "\n")

        return [result[0] for result in reranked_results]


if __name__ == '__main__':
    # Example usage
    reranker = Reranker()
    pairs = [['what is panda?', 'hi'],
             ['what is panda?', 'The giant panda (Ailuropoda melanoleuca), sometimes called apanda bear or simply panda, is a bear species endemic to China.']]
    scores = reranker.calculate_scores(pairs)
    print(scores)
