from smolagents import Tool
import os


class RecipeTool(Tool):
    name = "recipe_look_up"
    description = (
        "Uses string matching to retrieve a crafting recipe for an item in Minecraft."
    )
    inputs = {
        "item_name": {
            "type": "string",
            "description": "The item to look up in the form of lower_case_word.",
        }
    }
    output_type = "string"

    def __init__(self, directroy: str = "data/mc/recipe", **kwargs):

        super().__init__(**kwargs)
        self.recipe_files = [f.replace(".json", "") for f in os.listdir(
            directroy) if f.endswith('.json')]
        self.directroy = directroy

    def forward(self, item_name: str) -> str:
        assert isinstance(item_name, str), "Your item_name must be a string"

        item_name = item_name.lower()

        if item_name in self.recipe_files:
            with open(os.path.join(self.directroy, item_name + ".json"), "r") as f:
                return f"The crafting recipe for {item_name} is \n" + f.read() + \
                    "\n The pattern represents a 3x3 crafting table grid. \
                        If pattern does not show all 9 positions, if can be in any position while maintian the exact shape."
        else:
            item_name_parts = item_name.split("_")
            possible_matches = set()
            for part in item_name_parts:
                for recipe in self.recipe_files:
                    if part in recipe:
                        possible_matches.add(recipe.strip(".json"))

            return f"No exact match is found, but here are a list of possible matches:" + ", ".join(possible_matches)
