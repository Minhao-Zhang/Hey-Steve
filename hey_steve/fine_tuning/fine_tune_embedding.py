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
from utils import get_train_test, LinearAdapter, TripletDataset

# Load training and testing data
train_data, test_data = get_train_test()

# Initialize ChromaDB client and collection
client = chromadb.Client()
all_MiniLM_L6_v2_tuned = client.get_or_create_collection(
    name="all_MiniLM_L6_v2_tuned",
    embedding_function=SentenceTransformerEmbeddingFunction(
        "sentence-transformers/all-MiniLM-L6-v2", device="cuda")
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


def split_text_file_into_chunks(file_path="data/chunk_question_pairs/pg84.txt", chunk_size=1000):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    # Split the text into chunks of specified chunk_size characters
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    return chunks


# Get chunks from a random book (e.g., from Project Gutenberg)
frankenstein = split_text_file_into_chunks()


def random_negative():
    return random.choice(frankenstein)


def get_linear_schedule_with_warmup(optimizer, num_warmup_steps, num_training_steps):
    def lr_lambda(current_step):
        if current_step < num_warmup_steps:
            return float(current_step) / float(max(1, num_warmup_steps))
        return max(0.0, float(num_training_steps - current_step) / float(max(1, num_training_steps - num_warmup_steps)))
    return LambdaLR(optimizer, lr_lambda)


# Adapter training parameters
adapter_kwargs = {
    'num_epochs': 1000,
    'batch_size': 1024,
    'learning_rate': 0.003,
    'warmup_steps': 5,
    'max_grad_norm': 1.0,
    'margin': 1.0
}

base_model = SentenceTransformer('all-MiniLM-L6-v2')


def evaluate_adapter(validation_data, collection, base_model, adapter, k=10):
    hit_rates = []
    reciprocal_ranks = []

    for _, row in validation_data.iterrows():
        question = row['question']
        ground_truth = row['chunk']

        # Generate embedding for the question
        question_embedding = encode_query(question, base_model, adapter)
        # Retrieve documents using the embedding
        retrieved_docs = retrieve_documents_embeddings(
            collection, question_embedding, k)

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


def train_linear_adapter(base_model, train_data, negative_sampler, num_epochs=10, batch_size=32,
                         learning_rate=2e-5, warmup_steps=100, max_grad_norm=1.0, margin=1.0):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Initialize the LinearAdapter
    adapter = LinearAdapter(
        base_model.get_sentence_embedding_dimension()).to(device)

    # Define loss function and optimizer
    triplet_loss = nn.TripletMarginLoss(margin=margin, p=2)
    optimizer = AdamW(adapter.parameters(), lr=learning_rate)

    # Create dataset and dataloader
    dataset = TripletDataset(train_data, base_model, negative_sampler)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Calculate total number of training steps
    total_steps = len(dataloader) * num_epochs

    # Create learning rate scheduler
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps)

    # Training loop
    for epoch in range(num_epochs):
        total_loss = 0
        for batch in dataloader:
            query_emb, positive_emb, negative_emb = [
                x.to(device) for x in batch]

            # Forward pass
            adapted_query_emb = adapter(query_emb)
            # Compute loss
            loss = triplet_loss(adapted_query_emb, positive_emb, negative_emb)

            # Backward pass and optimization
            optimizer.zero_grad()
            loss.backward()
            clip_grad_norm_(adapter.parameters(), max_grad_norm)
            optimizer.step()
            scheduler.step()

            total_loss += loss.item()

        print(
            f"Epoch {epoch+1}/{num_epochs}, Loss: {total_loss/len(dataloader):.4f}")

        # Save the adapter state periodically
        if (epoch + 1) % 10 == 0:
            save_dict = {
                'adapter_state_dict': adapter.state_dict(),
                'adapter_kwargs': adapter_kwargs
            }
            torch.save(
                save_dict, f'models/mc_emb/adapters/linear_adapter_{epoch+1}.pth')
        if (epoch + 1) % 5 == 0:
            results = evaluate_adapter(
                test_cq, all_MiniLM_L6_v2_tuned, base_model, adapter, k=10)
            print(f"Average Hit Rate @10: {results['average_hit_rate']}")
            print(
                f"Mean Reciprocal Rank @10: {results['average_reciprocal_rank']}")


# Train the adapter using the defined parameters
train_linear_adapter(base_model, train_data, random_negative, **adapter_kwargs)
