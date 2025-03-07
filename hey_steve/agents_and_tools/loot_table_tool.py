
from smolagents import Tool
import os


class LootTableTool(Tool):
    name = "loot_table_look_up"
    description = (
        "Uses string matching to retrieve a the loot table (what you can get from performing the action) of an entity, blocks, and anything you can interact witht in Minecraft."
    )
    inputs = {
        "target_name": {
            "type": "string",
            "description": "The entity, block, or others in the form of lower_case_word.",
        }
    }
    output_type = "string"

    def __init__(self, directory: str = "data/mc/loot_table", **kwargs):
        super().__init__(**kwargs)
        self.directory = directory
        self.loot_table_files = self._get_all_loot_table_files(directory)

    def _get_all_loot_table_files(self, directory):
        """Recursively gets all JSON loot table files in the given directory and its subdirectories."""
        loot_table_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.json'):
                    loot_table_files.append(os.path.join(root, file))
        return loot_table_files

    def forward(self, target_name: str) -> str:
        assert isinstance(
            target_name, str), "Your target_name must be a string"

        target_name = target_name.lower()
        exact_match = None
        for loot_table_path in self.loot_table_files:
            loot_table_filename = os.path.basename(loot_table_path)
            if loot_table_filename == target_name + ".json":
                exact_match = loot_table_path
                break

        if exact_match:
            with open(exact_match, "r") as f:
                return f"The loot table for {target_name} is \n" + f.read()
        else:
            target_name_parts = target_name.split("_")
            possible_matches = set()
            for part in target_name_parts:
                for loot_table_path in self.loot_table_files:
                    loot_table_filename = os.path.basename(loot_table_path)
                    if part in loot_table_filename:
                        possible_matches.add(
                            loot_table_filename.strip(".json"))

            return f"No exact match is found, but here are a list of possible matches:" + ", ".join(possible_matches)
