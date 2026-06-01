import json
import os
from datetime import datetime


class ProjectManager:

    def __init__(self):

        self.file_path = (
            "data/memory/projects.json"
        )

        self.projects = {}

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

                        self.projects = (
                            json.loads(content)
                        )

                    else:

                        self.projects = {}

            except Exception:

                self.projects = {}

    def save(self):

        with open(
            self.file_path,
            "w"
        ) as f:

            json.dump(
                self.projects,
                f,
                indent=4
            )

    def create_project(
        self,
        name
    ):

        self.projects[name] = {
            "status": "active",
            "last_updated":
            datetime.now().isoformat()
        }

        self.save()

    def get_project(
        self,
        name
    ):

        return self.projects.get(name)

    def list_projects(self):

        return list(
            self.projects.keys()
        )

    def update_project(
        self,
        name,
        field,
        value
    ):

        if name in self.projects:

            self.projects[name][field] = value

            self.projects[name][
                "last_updated"
            ] = datetime.now().isoformat()

            self.save()
