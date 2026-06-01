class CharacterManager:

    def __init__(
        self,
        character
    ):

        self.character = character

    def get_name(self):

        return self.character["name"]

    def get_traits(self):

        return (
            self.character
            ["personality"]
            ["traits"]
        )

    def get_style(self):

        return (
            self.character
            ["personality"]
            ["speaking_style"]
        )

    def get_values(self):

        return (
            self.character
            ["values"]
        )

    def get_goals(self):

        return (
            self.character
            ["goals"]
        )

    def get_preferences(self):

        return (
            self.character
            ["preferences"]
        )