import json
import os

class CharacterLoader:

    def load(self, character_path):
        config_file = os.path.join(
            character_path,
            "character.json"
        )

        with open(config_file, "r") as f:
            data = json.load(f)

        # -----------------------------
        # Ensure emotion baselines exist
        # -----------------------------
        data["emotion_baselines"] = data.get(
            "emotion_baselines",
            {
                "mood": 0.6,
                "energy": 0.6,
                "engagement": 0.6,
                "patience": 0.6,
                "curiosity": 0.6,
            }
        )

        # Optional: attach derived metadata
        data["character_path"] = character_path

        return data