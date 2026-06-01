import json
import os
from datetime import datetime


class LifeEvents:

    def __init__(self):

        self.file_path = (
            "data/memory/life_events.json"
        )

        self.events = []

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

                    self.events = json.load(f)

            except Exception:

                self.events = []

    def save(self):

        with open(
            self.file_path,
            "w"
        ) as f:

            json.dump(
                self.events,
                f,
                indent=4
            )

    def add_event(
        self,
        description
    ):

        self.events.append(
            {
                "timestamp":
                datetime.now().isoformat(),

                "description":
                description
            }
        )

        self.save()

    def get_events(
        self
    ):

        return self.events