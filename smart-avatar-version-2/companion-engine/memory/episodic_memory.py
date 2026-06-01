import json
import os
from datetime import datetime


class EpisodicMemory:

    def __init__(self):

        self.file_path = (
            "data/memory/episodes.json"
        )

        self.episodes = []

        self.load()

    def load(self):

        if os.path.exists(
            self.file_path
        ):

            try:

                with open(
                    self.file_path,
                    "r"
                ) as f:

                    content = f.read().strip()

                    if content:

                        self.episodes = (
                            json.loads(content)
                        )

            except Exception:

                self.episodes = []

    def save(self):

        with open(
            self.file_path,
            "w"
        ) as f:

            json.dump(
                self.episodes,
                f,
                indent=4
            )

    def add_episode(
        self,
        summary
    ):

        self.episodes.append(
            {
                "timestamp":
                datetime.now().isoformat(),

                "summary":
                summary
            }
        )

        self.save()

    def get_recent(
        self,
        count=10
    ):

        return self.episodes[-count:]
