import json
import os

class CharacterLoader:

    def load(self, character_path):

        config_file = os.path.join(
            character_path,
            "character.json"
        )

        with open(config_file, "r") as f:
            return json.load(f)
