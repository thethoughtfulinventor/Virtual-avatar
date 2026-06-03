class IntentDetector:

    def detect(
        self,
        text
    ):

        text_lower = text.lower().strip()

        if text_lower.startswith(
            "remember "
        ):
            return "memory_store"

        if text_lower.startswith(
            "recall "
        ):
            return "memory_recall"

        if text_lower.startswith(
            "create project "
        ):
            return "project_create"

        if text_lower.startswith(
            "project "
        ):
            return "project_lookup"

        if text_lower in [
            "hi",
            "hello",
            "hey"
        ]:
            return "greeting"

        if text_lower == "episodes":
            return "episode_list"

        if text_lower.startswith("episode "):
            return "episode_create"

        if text_lower == "context":
            return "context_view"

        if text_lower == "clear context":
            return "context_clear"

        if text_lower == "projects":
            return "projects_list"

        if text_lower == "life events":
            return "life_events_list"

        if text_lower.startswith("life event "):
            return "life_event_create"

        if text_lower == "state":
            return "state_view"

        # Character switching
        # Supports: "switch to Aiya"
        #           "switch character Pyrus"
        if (
            text_lower.startswith("switch to ")
            or text_lower.startswith("switch character ")
        ):
            return "switch_character"

        return "conversation"