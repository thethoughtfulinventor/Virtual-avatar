class CharacterManager:
 
    def __init__(
        self,
        character
    ):
 
        self.character = character
 
    def get_name(self):
 
        return self.character["name"]
 
    def get_traits(self):
        # Get the general traits list (default to empty list if missing)
        general_traits = self.character.get("personality", {}).get("traits", [])
        
        # Get the specific personality quirks list (default to empty list if missing)
        quirks = self.character.get("personality_quirks", [])
        
        # Combine both lists and return
        return general_traits + quirks   
 
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
    
    def get_personality_quirks(self):
        return (
            self.character
            .get("personality_quirks", [])
        )