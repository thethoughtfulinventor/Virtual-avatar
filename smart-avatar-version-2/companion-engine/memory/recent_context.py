import json
import os


class RecentContext:

    def __init__(
        self,
        max_entries=50
    ):

        self.max_entries = max_entries

        self.file_path = (
            "data/memory/recent_context.json"
        )

        self.entries = []

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

                        self.entries = (
                            json.loads(content)
                        )

            except Exception:

                self.entries = []

    def save(self):

        with open(
            self.file_path,
            "w"
        ) as f:

            json.dump(
                self.entries,
                f,
                indent=4
            )

    def add(
        self,
        role,
        content
    ):

        self.entries.append(
            {
                "role": role,
                "content": content
            }
        )

        if len(
            self.entries
        ) > self.max_entries:

            self.entries.pop(0)

        self.save()

    def get_recent(
        self,
        count=10
    ):

        return self.entries[-count:]

    def clear(self):

        self.entries = []

        self.save()