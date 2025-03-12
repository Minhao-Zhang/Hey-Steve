import json
import os
import tiktoken
import matplotlib.pyplot as plt
import numpy as np

FIGURE_BASE_PATH = "hey_steve/processing/images"


def remove_outliers(data):
    """
    Removes outliers from a list of numerical data using the 3 standard deviations method.
    """
    data = np.array(data)
    mean = np.mean(data)
    std_dev = np.std(data)
    if std_dev == 0:  # prevent division by zero if no std dev
        return data.tolist()

    # Filter data to keep only points within 3 standard deviations
    filtered_data = data[np.abs(data - mean) <= 3 * std_dev]
    return filtered_data.tolist()


def calculate_statistics(data, data_type="character"):
    """
    Calculates and prints statistics for the given data.
    """
    data_np = np.array(data)
    mean_val = np.mean(data_np)
    median_val = np.median(data_np)
    std_dev_val = np.std(data_np)
    min_val = np.min(data_np)
    max_val = np.max(data_np)

    print(f"\n--- {data_type.capitalize()} Length Statistics ---")
    print(f"Mean: {mean_val:.2f}")
    print(f"Median: {median_val:.2f}")
    print(f"Standard Deviation: {std_dev_val:.2f}")
    print(f"Min: {min_val}")
    print(f"Max: {max_val}")


def read_json_files_from_directory(dir_path):
    """
    Reads all json files in a directory and groups them into one list.
    """
    all_chunks = []
    for filename in os.listdir(dir_path):
        if filename.endswith(".json"):
            filepath = os.path.join(dir_path, filename)
            with open(filepath, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_chunks.extend(data)
                elif isinstance(data, dict):
                    all_chunks.append(data)  # in case json is a dict
    return all_chunks


def plot_character_length_distribution(chunks):
    """
    Plots the distribution of character length by chunks.
    """
    char_lengths = []
    for chunk in chunks:
        if isinstance(chunk, str):
            char_lengths.append(len(chunk))
        elif isinstance(chunk, dict) and 'text' in chunk:
            char_lengths.append(len(chunk['text']))

    calculate_statistics(char_lengths, data_type="character")

    filtered_char_lengths = remove_outliers(char_lengths)
    calculate_statistics(filtered_char_lengths,
                         data_type="character (outliers removed)")

    plt.figure(figsize=(10, 6))
    plt.hist(filtered_char_lengths, bins=50)  # Use bin of 50
    plt.title('Distribution of Character Lengths of Chunks (Outliers Removed)')
    plt.xlabel('Character Length')
    plt.ylabel('Frequency')
    # Save plot to the images directory
    os.makedirs(FIGURE_BASE_PATH, exist_ok=True)  # Ensure directory exists
    filepath = os.path.join(FIGURE_BASE_PATH, 'char_length_distribution.png')
    plt.savefig(filepath)
    plt.close()  # Close plot to prevent display


def count_tokens_per_chunk(chunks):
    """
    Counts how many tokens would there be for each chunk using tiktoken.
    """
    encoding = tiktoken.get_encoding("cl100k_base")  # or another encoding
    token_counts = []
    for chunk in chunks:
        if isinstance(chunk, str):
            tokens_per_chunk = encoding.encode(chunk)
        elif isinstance(chunk, dict) and 'text' in chunk:
            tokens_per_chunk = encoding.encode(chunk['text'])
        token_counts.append(len(tokens_per_chunk))
    return token_counts


def plot_token_length_distribution(token_counts):
    """
    Plots histogram of token lengths.
    """
    calculate_statistics(token_counts, data_type="token")

    filtered_token_counts = remove_outliers(token_counts)
    calculate_statistics(filtered_token_counts,
                         data_type="token (outliers removed)")

    plt.figure(figsize=(10, 6))
    plt.hist(filtered_token_counts, bins=50)
    plt.title('Distribution of Token Lengths of Chunks (Outliers Removed)')
    plt.xlabel('Token Length')
    plt.ylabel('Frequency')
    # Save plot to the images directory
    os.makedirs(FIGURE_BASE_PATH, exist_ok=True)  # Ensure directory exists
    filepath = os.path.join(FIGURE_BASE_PATH, 'token_length_distribution.png')
    plt.savefig(filepath)
    plt.close()  # Close plot to prevent display


if __name__ == "__main__":
    dir_path = 'data/chunks_ftc/'  # Use data/chunks directory
    chunks = read_json_files_from_directory(dir_path)
    plot_character_length_distribution(chunks)
    token_counts = count_tokens_per_chunk(chunks)
    plot_token_length_distribution(token_counts)
