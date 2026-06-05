from emotion.emotional_state import EmotionalState
from emotion.emotional_analyzer import EmotionalAnalyzer
 
 
class EmotionalManager:
 
    def __init__(
        self,
        character_name
    ):
 
        self.emotional_state = (
            EmotionalState(character_name)
        )
 
        self.emotional_analyzer = (
            EmotionalAnalyzer()
        )
 
        print(
            f"Emotional state loaded "
            f"for {character_name}"
        )
 
    def process(
        self,
        text,
        intent,
        character_manager
    ):
 
        deltas = (
            self.emotional_analyzer
            .analyze(
                text,
                intent,
                character_manager
            )
        )

        print(
            f"[Emotion] deltas={deltas}"
        )
 
        self.emotional_state.apply_delta(
            deltas
        )
        print(
            f"[Emotion] active="
            f"{character_manager.get_name()}"
        )

        print(
            f"[Emotion] state db="
            f"{self.emotional_state.db_path}"
        )
 
    def get_dominant(self):
 
        return (
            self.emotional_state
            .get_dominant()
        )
 
    def get_all(self):
 
        return (
            self.emotional_state
            .get_all()
        )
 