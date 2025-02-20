import pandas as pd

# mc_qa = pd.read_json("hf://datasets/naklecha/minecraft-question-answer-700k/train.json")
mc_qa = pd.read_json("data/hf/minecraft-question-answer-700k.json")

# remove Non-Java version of Minecraft
removal = ["Bedrock_", "Alpha_", "Beta_", "Classic_", "Console_", "Education_",
           "Element", 'Launcher_', "MinecraftEdu_", "PlayStation_",
           "Pocket_", "Wii_", "XBox_", "Dungeons", "Indev_", "Infdev_",
           "Minecraft_Wiki", "Nintendo_", "Programs_and_editors"]

for rem in removal:
    mc_qa = mc_qa[~mc_qa['source'].str.contains(rem, na=False)]

# Group by source, count rows, and sort by count
source_counts = mc_qa.groupby('source').size().sort_values()

# Filter groups with size less than 20
sources_to_remove = source_counts[source_counts < 20].index.tolist()

# Remove rows with sources in the sources_to_remove list
mc_qa = mc_qa[~mc_qa['source'].isin(sources_to_remove)]

mc_qa.to_json("data/hf/minecraft-question-answer-700k-cleaned-609k.json")
