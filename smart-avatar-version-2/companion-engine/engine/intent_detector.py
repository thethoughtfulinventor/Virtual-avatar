
class IntentDetector:
 
    def detect(
        self,
        text
    ):
 
        text = text.lower()
 
        if text.startswith(
            "remember "
        ):
            return "memory_store"
 
        if text.startswith(
            "recall "
        ):
            return "memory_recall"
 
        if text.startswith(
            "create project "
        ):
            return "project_create"
 
        if text.startswith(
            "project "
        ):
            return "project_lookup"
 
        if text in [
            "hi",
            "hello",
            "hey"
        ]:
            return "greeting"
 
        if text == "episodes":
            return "episode_list"
 
        if text.startswith("episode "):
            return "episode_create"
 
        if text == "context":
            return "context_view"
 
        if text == "clear context":
            return "context_clear"
 
        if text == "projects":
            return "projects_list"
 
        if text == "life events":
            return "life_events_list"
 
        if text.startswith("life event "):
            return "life_event_create"
 
        return "conversation"
 