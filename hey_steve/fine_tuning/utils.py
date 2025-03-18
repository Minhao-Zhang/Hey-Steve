import json
import os


def combine_json_files(input_dir, output_path):
    """
    Reads all json files in a given directory. These json files will only contain
    list of strings in json format. Combine them together and store them into
    a new file that the user provides a path for.

    Args:
        input_dir (str): The directory containing the json files.
        output_path (str): The path to the output json file.
    """
    combined_list = []
    for filename in os.listdir(input_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(input_dir, filename)
            with open(file_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list) and all(isinstance(item, str) for item in data):
                    combined_list.extend(data)
                else:
                    print(
                        f"Warning: Skipping file {filename} as it does not contain a list of strings.")

    with open(output_path, 'w') as f:
        json.dump(combined_list, f, indent=4)


if __name__ == '__main__':
    input_directory = "data/chunks_custom"  # Replace with your input directory
    # Replace with your desired output path
    output_file_path = "data/chunk_question_pairs_new/all_chunks.json"
    combine_json_files(input_directory, output_file_path)
    print(f"Combined JSON data saved to {output_file_path}")
