class EmotionalAnalyzer:
 
    def analyze(
        self,
        text,
        intent,
        character_manager
    ):
 
        deltas = {
            "mood": 0.0,
            "energy": 0.0,
            "engagement": 0.0,
            "patience": 0.0,
            "curiosity": 0.0
        }
 
        # Passive energy drain every interaction
        deltas["energy"] -= 0.02
 
        self._apply_intent_deltas(
            intent,
            deltas
        )
 
        self._apply_keyword_deltas(
            text,
            character_manager,
            deltas
        )
 
        return deltas
 
    def _apply_intent_deltas(
        self,
        intent,
        deltas
    ):
 
        # Positive intents
        if intent == "greeting":
            deltas["mood"] += 0.03
 
        if intent == "conversation":
            deltas["engagement"] += 0.02
 
        # Routine system commands
        # slightly drain engagement
        if intent in [
            "episode_list",
            "context_view",
            "context_clear",
            "projects_list",
            "life_events_list"
        ]:
            deltas["engagement"] -= 0.02
 
    def _apply_keyword_deltas(
        self,
        text,
        character_manager,
        deltas
    ):
 
        likes = character_manager.get_likes()
        dislikes = character_manager.get_dislikes()
        interests = character_manager.get_interests()
 
        if self._matches_any(text, likes):
            deltas["mood"] += 0.04
            deltas["engagement"] += 0.06
            deltas["curiosity"] += 0.02
 
        if self._matches_any(text, interests):
            deltas["curiosity"] += 0.05
            deltas["engagement"] += 0.03
 
        if self._matches_any(text, dislikes):
            deltas["patience"] -= 0.06
            deltas["mood"] -= 0.03
            deltas["engagement"] -= 0.04
 
    def _matches_any(
        self,
        text,
        phrases
    ):
 
        text_lower = text.lower()
 
        for phrase in phrases:
 
            if phrase.lower() in text_lower:
                return True
 
        return False
 