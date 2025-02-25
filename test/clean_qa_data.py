import pandas as pd

# mc_qa = pd.read_json("hf://datasets/naklecha/minecraft-question-answer-700k/train.json")
mc_qa = pd.read_json("data/hf/minecraft-question-answer-700k.json")


def remove_irrelevant():
    # remove Non-Java version of Minecraft
    removal = ["Bedrock_", "Alpha_", "Beta_", "Classic_", "Console_", "Education_",
               "Element", 'Launcher_', "MinecraftEdu_", "PlayStation_",
               "Pocket_", "Wii_", "XBox_", "Dungeons", "Indev_", "Infdev_",
               "Minecraft_Wiki", "Nintendo_", "Programs_and_editors"]

    for rem in removal:
        mc_qa_filtered = mc_qa[~mc_qa['source'].str.contains(rem, na=False)]

    # Group by source, count rows, and sort by count
    source_counts = mc_qa_filtered.groupby('source').size().sort_values()

    # Filter groups with size less than 20
    sources_to_remove = source_counts[source_counts < 20].index.tolist()

    # Remove rows with sources in the sources_to_remove list
    mc_qa_filtered = mc_qa_filtered[~mc_qa_filtered['source'].isin(
        sources_to_remove)]
    print(f"The resulting table has {len(mc_qa_filtered)} rows.")

    mc_qa_filtered.to_json(
        "data/hf/minecraft-question-answer-700k-cleaned-609k.json")


def keep_relevant():
    import os

    urls_dir = "urls"
    base_url = "https://minecraft.wiki/w/"
    all_urls = []

    for filename in os.listdir(urls_dir):
        filepath = os.path.join(urls_dir, filename)
        if os.path.isfile(filepath):
            with open(filepath, "r") as f:
                for line in f:
                    url = base_url + line.strip()
                    all_urls.append(url)

    # Filter the mc_qa dataframe
    mc_qa_filtered = mc_qa[mc_qa['source'].isin(all_urls)]
    print(f"The resulting table has {len(mc_qa_filtered)} rows.")

    # Save the filtered dataframe to a new json file
    mc_qa_filtered.to_json(
        "data/hf/minecraft-question-answer-700k-indomain.json")


if __name__ == "__main__":
    remove_irrelevant()
    keep_relevant()
