import os
import json


class CharacterRoster:
    """
    Loads all available character definitions
    at startup.

    Used by the Planner for routing decisions
    and by Brain for mid-session switching.
    """

    def __init__(
        self,
        characters_dir="characters"
    ):

        self.characters_dir = characters_dir
        self.roster = {}
        self._load_all()

    def _load_all(self):

        if not os.path.exists(
            self.characters_dir
        ):
            return

        for entry in sorted(
            os.listdir(self.characters_dir)
        ):

            char_path = os.path.join(
                self.characters_dir,
                entry
            )

            config_path = os.path.join(
                char_path,
                "character.json"
            )

            if (
                os.path.isdir(char_path)
                and os.path.exists(config_path)
            ):

                try:

                    with open(
                        config_path, "r"
                    ) as f:

                        self.roster[entry] = (
                            json.load(f)
                        )

                        print(
                            f"[Roster] Loaded: {entry}"
                        )

                except Exception as e:

                    print(
                        f"[Roster] Failed to load "
                        f"{entry}: {e}"
                    )

    def get(self, name):
        """
        Returns character data by name.
        Case-insensitive.
        """

        for key, val in self.roster.items():

            if key.lower() == name.lower():
                return val

        return None

    def resolve_name(self, name):
        """
        Returns the canonical directory name
        for a given input string.
        Case-insensitive. Returns None if not found.
        """

        for key in self.roster.keys():

            if key.lower() == name.lower():
                return key

        return None

    def get_names(self):
        return list(self.roster.keys())

    def get_all(self):
        return self.roster

    def get_summary(self, exclude=None):
        """
        Returns a compact description of each
        character suitable for inclusion in
        LLM planning prompts.

        exclude: character name to omit
                 (usually the active character)
        """

        lines = []

        for name, data in self.roster.items():

            if (
                exclude
                and name.lower() == exclude.lower()
            ):
                continue

            personality = data.get(
                "personality", {}
            )
            traits = personality.get("traits", [])
            style = personality.get(
                "speaking_style", ""
            )
            interests = data.get("interests", [])
            likes = data.get("likes", [])
            dislikes = data.get("dislikes", [])

            lines.append(
                f"- {name}: "
                f"style={style}, "
                f"traits={', '.join(traits)}, "
                f"interests={', '.join(interests[:3])}, "
                f"likes={', '.join(likes[:2])}, "
                f"dislikes={', '.join(dislikes[:2])}"
            )

        if not lines:
            return "No other characters available."

        return "\n".join(lines)