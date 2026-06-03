class IntentDetector:

    def detect(self, text):

        t = text.lower().strip()

        if t.startswith("remember "):
            return "memory_store"

        if t.startswith("recall "):
            return "memory_recall"

        if t.startswith("create project "):
            return "project_create"

        if t.startswith("project "):
            return "project_lookup"

        if t in ["hi", "hello", "hey"]:
            return "greeting"

        if t == "episodes":
            return "episode_list"

        if t.startswith("episode "):
            return "episode_create"

        if t == "context":
            return "context_view"

        # Natural language variations for clear context
        if any(phrase in t for phrase in [
            "clear context",
            "clear the context",
            "clear our context",
            "reset context",
            "wipe context",
            "forget our conversation",
            "start fresh",
            "start over",
            "clear conversation",
        ]):
            return "context_clear"

        if t == "projects":
            return "projects_list"

        if t == "life events":
            return "life_events_list"

        if t.startswith("life event "):
            return "life_event_create"

        if t == "state":
            return "state_view"

        # Natural language variations for clear episodes
        if any(phrase in t for phrase in [
            "clear episodes",
            "clear episodic",
            "clear memories",
            "wipe episodes",
            "delete episodes",
            "forget everything",
        ]):
            return "episode_clear"

        if (
            t.startswith("switch to ")
            or t.startswith("switch character ")
        ):
            return "switch_character"

        return "conversation"