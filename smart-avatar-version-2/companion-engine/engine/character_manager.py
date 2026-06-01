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
 
    def get_emotional_modifiers(self):
 
        return (
            self.character
            .get("emotional_modifiers", {})
        )
 
    def get_likes(self):
 
        return (
            self.character
            .get("likes", [])
        )
 
    def get_dislikes(self):
 
        return (
            self.character
            .get("dislikes", [])
        )
 
    def get_interests(self):
 
        return (
            self.character
            .get("interests", [])
        )