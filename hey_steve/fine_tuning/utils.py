from torch import nn
from torch.utils.data import Dataset, DataLoader
import json
import os
from typing import Tuple

import pandas as pd
from sklearn.model_selection import train_test_split


def read_all_cq_json(data_dir="data/chunk_question_pairs"):
    all_files = os.listdir(data_dir)
    cq_files = [f for f in all_files if f.startswith(
        "cq_") and f.endswith(".json")]
    cq_files.sort(key=lambda x: int(x.split("_")[1].split(".")[0]))

    concatenated_data = []
    for file in cq_files:
        file_path = os.path.join(data_dir, file)
        with open(file_path, 'r') as f:
            data = json.load(f)
            concatenated_data.extend(data)
    return concatenated_data


def get_train_test(data_dir="data/chunk_question_pairs") -> Tuple[pd.DataFrame, pd.DataFrame]:
    data = read_all_cq_json(data_dir)
    data = pd.DataFrame(data)
    train_data, test_data = train_test_split(
        data, test_size=0.2, random_state=0)
    return train_data, test_data


class LinearAdapter(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.linear = nn.Linear(input_dim, input_dim)

    def forward(self, x):
        return self.linear(x)


class TripletDataset(Dataset):
    def __init__(self, data, base_model, negative_sampler):
        self.data = data
        self.base_model = base_model
        self.negative_sampler = negative_sampler

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data.iloc[idx]
        query = item['question']
        positive = item['chunk']
        negative = self.negative_sampler()

        query_emb = self.base_model.encode(query, convert_to_tensor=True)
        positive_emb = self.base_model.encode(positive, convert_to_tensor=True)
        negative_emb = self.base_model.encode(negative, convert_to_tensor=True)

        return query_emb, positive_emb, negative_emb
