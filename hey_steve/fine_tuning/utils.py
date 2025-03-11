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
        self.linear = nn.Linear(input_dim, 1024)
        self.linear2 = nn.Linear(1024, input_dim)

    def forward(self, x):
        x = self.linear(x)
        return self.linear2(x)


if __name__ == "__main__":
    train, test = get_train_test()
    train.to_json("data/chunk_question_pairs/mc_cq_train.json")
    test.to_json("data/chunk_question_pairs/mc_cq_test.json")
