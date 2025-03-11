from utils import get_train_test
from torch.utils.data import DataLoader, Dataset
import numpy as np
import random
import torch
from torch import nn
from torch.utils.data import DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import LambdaLR
from torch.nn.utils import clip_grad_norm_
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

import chromadb
from chromadb.utils.embedding_functions.sentence_transformer_embedding_function import SentenceTransformerEmbeddingFunction
from utils import get_train_test, LinearAdapter

# Load training and testing data
train_data, test_data = get_train_test()

# Initialize ChromaDB client and collection
client = chromadb.Client()
all_MiniLM_L6_v2_tuned = client.get_or_create_collection(
    name="all-mpnet-base-v2_tuned",
    embedding_function=SentenceTransformerEmbeddingFunction(
        "all-mpnet-base-v2", device="cuda")
)


def reciprocal_rank(retrieved_docs, ground_truth, k):
    try:
        rank = retrieved_docs.index(ground_truth) + 1
        return 1.0 / rank if rank <= k else 0.0
    except ValueError:
        return 0.0


def hit_rate(retrieved_docs, ground_truth, k):
    return 1.0 if ground_truth in retrieved_docs[:k] else 0.0


def encode_query(query, base_model, adapter):
    device = next(adapter.parameters()).device
    query_emb = base_model.encode(query, convert_to_tensor=True).to(device)
    adapted_query_emb = adapter(query_emb)
    return adapted_query_emb.cpu().detach().numpy()


# Load chunk question pairs data
train_cq, test_cq = get_train_test("data/chunk_question_pairs")
all_chunks = train_cq['chunk'].tolist() + test_cq['chunk'].tolist()


def retrieve_documents_embeddings(collection, query_embedding, k=10):
    query_embedding_list = query_embedding.tolist()
    results = collection.query(
        query_embeddings=[query_embedding_list], n_results=k)
    return results['documents'][0]


def insert_documents(collection, all_chunks):
    for i, chunk in enumerate(tqdm(all_chunks)):
        collection.add(documents=[chunk], ids=[f"chunk_{i}"])


insert_documents(all_MiniLM_L6_v2_tuned, all_chunks)


def validate_embedding_model(validation_data, collection, k=10):
    hit_rates = []
    reciprocal_ranks = []

    for _, row in validation_data.iterrows():
        question = row['question']
        ground_truth = row['chunk']

        results = collection.query(
            query_texts=[question],
            n_results=k
        )

        retrieved_docs = results["documents"][0]

        # Calculate metrics
        hr = hit_rate(retrieved_docs, ground_truth, k)
        rr = reciprocal_rank(retrieved_docs, ground_truth, k)

        hit_rates.append(hr)
        reciprocal_ranks.append(rr)

    # Calculate average metrics
    avg_hit_rate = np.mean(hit_rates)
    avg_reciprocal_rank = np.mean(reciprocal_ranks)

    return {
        'average_hit_rate': avg_hit_rate,
        'average_reciprocal_rank': avg_reciprocal_rank
    }


results = validate_embedding_model(train_cq, all_MiniLM_L6_v2_tuned, k=10)
print("Train Set:")
print(f"Average Hit Rate @10: {results['average_hit_rate']}")
print(f"Mean Reciprocal Rank @10: {results['average_reciprocal_rank']}")

print("Test set")
results = validate_embedding_model(test_cq, all_MiniLM_L6_v2_tuned, k=10)
print(f"Average Hit Rate @10: {results['average_hit_rate']}")
print(f"Mean Reciprocal Rank @10: {results['average_reciprocal_rank']}")


def split_text_file_into_chunks(file_path="data/chunk_question_pairs/pg84.txt", max_char=1000, overlap=300):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    # Split the text into chunks of specified chunk_size characters with overlap
    chunks = [text[i:i + max_char]
              for i in range(0, len(text), max_char - overlap) if i + max_char <= len(text)]
    if len(text) % (max_char - overlap) != 0:
        chunks.append(text[len(text) - max_char:])  # add last chunk
    return chunks


# Get chunks from a random book (e.g., from Project Gutenberg)
frankenstein = split_text_file_into_chunks()

# ================== Precompute Embeddings ==================


class PrecomputedTripletDataset(Dataset):
    def __init__(self, query_embs, positive_embs, negative_embs):
        self.query_embs = query_embs
        self.positive_embs = positive_embs
        self.negative_embs = negative_embs

    def __len__(self):
        return len(self.query_embs)

    def __getitem__(self, idx):
        neg_idx = random.randint(0, len(self.negative_embs)-1)
        return (
            self.query_embs[idx],
            self.positive_embs[idx],
            self.negative_embs[neg_idx]
        )


def precompute_embeddings(base_model, data, negative_chunks):
    # Batch encode all data
    with torch.no_grad():
        query_embs = torch.tensor(base_model.encode(data['question'].tolist()))
        positive_embs = torch.tensor(base_model.encode(data['chunk'].tolist()))
        negative_embs = torch.tensor(base_model.encode(negative_chunks))
    return query_embs, positive_embs, negative_embs

# ================== Optimized Training Setup ==================


def get_linear_schedule_with_warmup(optimizer, num_warmup_steps, num_training_steps):
    def lr_lambda(current_step):
        if current_step < num_warmup_steps:
            return float(current_step) / float(max(1, num_warmup_steps))
        return max(0.0, float(num_training_steps - current_step) / float(max(1, num_training_steps - num_warmup_steps)))
    return LambdaLR(optimizer, lr_lambda)


class ChromaEvaluator:
    def __init__(self, collection, train_data, test_data, base_model, device):
        self.collection = collection
        self.train_data = train_data
        self.test_data = test_data
        self.base_model = base_model
        self.device = device
        self.train_ground_truths = train_data['chunk'].tolist()
        self.test_ground_truths = test_data['chunk'].tolist()

        # Precompute all questions
        with torch.no_grad():
            self.train_questions = train_data['question'].tolist()
            self.test_questions = test_data['question'].tolist()
            self.train_question_embs = torch.tensor(
                base_model.encode(self.train_questions))
            self.test_question_embs = torch.tensor(
                base_model.encode(self.test_questions))

    def evaluate(self, adapter, k=10, batch_size=1024):
        adapter.eval()

        train_metrics = self._evaluate_split(
            adapter, self.train_question_embs, self.train_ground_truths, k, batch_size)
        test_metrics = self._evaluate_split(
            adapter, self.test_question_embs, self.test_ground_truths, k, batch_size)

        return {
            'train': train_metrics,
            'test': test_metrics
        }

    def _evaluate_split(self, adapter, question_embs, ground_truths, k, batch_size):
        all_adapted = []

        # Batch process all questions
        with torch.no_grad():
            for i in range(0, len(question_embs), batch_size):
                batch = question_embs[i:i+batch_size].to(self.device)
                all_adapted.append(adapter(batch).cpu())

        adapted_embs = torch.cat(all_adapted).numpy()

        # Batch query ChromaDB
        results = self.collection.query(
            query_embeddings=adapted_embs.tolist(),
            n_results=k,
            include=['documents']
        )

        # Calculate metrics
        hit_rates = []
        reciprocal_ranks = []

        for idx, docs in enumerate(results['documents']):
            hr = 1.0 if ground_truths[idx] in docs else 0.0
            hit_rates.append(hr)

            try:
                rank = docs.index(ground_truths[idx]) + 1
                reciprocal_ranks.append(1.0/rank if rank <= k else 0.0)
            except ValueError:
                reciprocal_ranks.append(0.0)

        return {
            'average_hit_rate': np.mean(hit_rates),
            'average_reciprocal_rank': np.mean(reciprocal_ranks)
        }

# ================== Main Training Function ==================


def train_linear_adapter(base_model, train_data, test_data, all_negative_chunks,
                         num_epochs=1000, batch_size=1024, learning_rate=3e-3,
                         warmup_steps=5, max_grad_norm=1.0, margin=1.0):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Precompute all embeddings
    print("Precomputing embeddings...")
    query_embs, positive_embs, negative_embs = precompute_embeddings(
        base_model, train_data, all_negative_chunks
    )

    # Create dataset and dataloader with pinned memory
    dataset = PrecomputedTripletDataset(
        query_embs, positive_embs, negative_embs)
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=4,
        pin_memory=True,
        persistent_workers=True
    )

    # Initialize model and optimizer
    adapter = LinearAdapter(
        base_model.get_sentence_embedding_dimension()).to(device)
    optimizer = AdamW(adapter.parameters(), lr=learning_rate)
    triplet_loss = nn.TripletMarginLoss(margin=margin, p=2)

    # Scheduler
    total_steps = len(dataloader) * num_epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer, warmup_steps, total_steps)

    # Initialize evaluator
    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection(
        name="all-mpnet-base-v2_tuned",
        embedding_function=SentenceTransformerEmbeddingFunction(
            "all-mpnet-base-v2", device="cuda"
        )
    )

    evaluator = ChromaEvaluator(
        collection, train_data, test_data, base_model, device)

    # Training loop
    for epoch in range(num_epochs):
        adapter.train()
        total_loss = 0

        for batch in dataloader:
            q, p, n = [t.to(device, non_blocking=True) for t in batch]

            adapted_q = adapter(q)
            loss = triplet_loss(adapted_q, p, n)

            # Backward pass and optimization
            optimizer.zero_grad()
            loss.backward()

            # Gradient clipping
            clip_grad_norm_(adapter.parameters(), max_grad_norm)
            optimizer.step()
            scheduler.step()

            total_loss += loss.item()

        print(
            f"Epoch {epoch+1}/{num_epochs}, Loss: {total_loss/len(dataloader):.4f}")

        # Evaluation
        if (epoch + 1) % 5 == 0:
            eval_results = evaluator.evaluate(adapter)
            print(f"\nEvaluation after epoch {epoch+1}:")
            print("Train Set:")
            print(
                f"  Avg Hit Rate@10: {eval_results['train']['average_hit_rate']:.4f}")
            print(
                f"  Avg MRR@10: {eval_results['train']['average_reciprocal_rank']:.4f}")
            print("Test Set:")
            print(
                f"  Avg Hit Rate@10: {eval_results['test']['average_hit_rate']:.4f}")
            print(
                f"  Avg MRR@10: {eval_results['test']['average_reciprocal_rank']:.4f}")
            print(f"Training Loss: {total_loss/len(dataloader):.4f}\n")

        # Save checkpoint
        # if (epoch + 1) % 10 == 0:
        #     torch.save({
        #         'adapter': adapter.state_dict(),
        #         'optimizer': optimizer.state_dict(),
        #         'scheduler': scheduler.state_dict(),
        #     }, f"adapter_epoch_{epoch+1}.pth")


# ================== Execution ==================
if __name__ == "__main__":
    # Load data
    train_data, test_data = get_train_test()
    frankenstein_chunks = split_text_file_into_chunks()

    # Initialize base model
    base_model = SentenceTransformer('all-mpnet-base-v2')

    # Training parameters
    adapter_kwargs = {
        'num_epochs': 200,
        'batch_size': 1024,  # Increased batch size for VRAM utilization
        'learning_rate': 0.003,
        'warmup_steps': 5,
        'max_grad_norm': 1.0,
        'margin': 1.0
    }

    # Start training
    train_linear_adapter(
        base_model=base_model,
        train_data=train_data,
        test_data=test_data,
        all_negative_chunks=frankenstein_chunks,
        **adapter_kwargs
    )
