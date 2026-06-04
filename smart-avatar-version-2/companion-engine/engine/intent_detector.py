import re


class IntentDetector:
    """
    Maps user input to a canonical intent string.

    v2 changes
    ----------
    - Added natural-language variants for every intent so
      users aren't forced into rigid `remember key=value`
      or `create project X` syntax.
    - Extracted pattern tables so adding new variants
      doesn't require editing flow-control logic.
    - Pre-compiled all regex for speed (called every turn).
    - clear_context and clear_episodes patterns are now
      regex-based so partial matches can't mis-fire.
    """

    # --------------------------------------------------
    # Pattern tables
    # (checked in order; first match wins)
    # --------------------------------------------------

    # Patterns that MUST start the utterance
    _PREFIX_INTENTS = [
        ("memory_store",    r"^remember\s+\w"),
        ("memory_store",    r"^store\s+"),
        ("memory_recall",   r"^recall\s+"),
        ("memory_recall",   r"^what\s+(do\s+you\s+know|have\s+you\s+stored|did\s+i\s+tell\s+you)\b"),
        ("project_create",  r"^create\s+project\s+\w"),
        ("project_create",  r"^(start|new|add)\s+project\s+\w"),
        ("project_lookup",  r"^project\s+\w"),
        ("episode_create",  r"^episode\s+\w"),
        ("life_event_create", r"^life\s+event\s+\w"),
        ("switch_character", r"^switch\s+(to|character)\s+\w"),
    ]

    # Exact / whole-utterance matches
    _EXACT_INTENTS = {
        "hi":           "greeting",
        "hello":        "greeting",
        "hey":          "greeting",
        "hey there":    "greeting",
        "good morning": "greeting",
        "good evening": "greeting",
        "sup":          "greeting",
        "yo":           "greeting",
        "episodes":     "episode_list",
        "context":      "context_view",
        "projects":     "projects_list",
        "life events":  "life_events_list",
        "state":        "state_view",
        "status":       "state_view",
        "emotional state": "state_view",
        "my memories":  "episode_list",
    }

    # Substring / contains-anywhere patterns
    _CONTAINS_INTENTS = [
        # context_clear
        ("context_clear", [
            "clear context", "clear the context",
            "clear our context", "reset context",
            "wipe context", "forget our conversation",
            "start fresh", "start over",
            "clear conversation", "new conversation",
        ]),
        # episode_clear
        ("episode_clear", [
            "clear episodes", "clear episodic",
            "clear memories", "wipe episodes",
            "delete episodes", "forget everything",
            "erase memories",
        ]),
        # greetings (partial, lower priority)
        ("greeting", [
            "good morning", "good afternoon",
            "good evening", "good night",
        ]),
        # project list
        ("projects_list", [
            "list my projects", "show my projects",
            "what projects", "all projects",
        ]),
        # life events list
        ("life_events_list", [
            "list life events", "show life events",
            "my life events",
        ]),
    ]

    # Compiled prefix patterns (done once at class level)
    _COMPILED_PREFIXES = [
        (intent, re.compile(pattern, re.IGNORECASE))
        for intent, pattern in _PREFIX_INTENTS
    ]

    # Flattened contains-set for O(1) substring check
    _CONTAINS_MAP: dict  # built in __init__

    def __init__(self):
        # Build a flat dict: phrase → intent
        self._phrase_to_intent: dict[str, str] = {}
        for intent, phrases in self._CONTAINS_INTENTS:
            for phrase in phrases:
                self._phrase_to_intent[phrase] = intent

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def detect(self, text: str) -> str:
        t = text.strip()
        t_lower = t.lower()

        # 1. Exact match (fastest)
        if t_lower in self._EXACT_INTENTS:
            return self._EXACT_INTENTS[t_lower]

        # 2. Prefix regex
        for intent, pattern in self._COMPILED_PREFIXES:
            if pattern.match(t):
                return intent

        # 3. Substring containment
        for phrase, intent in self._phrase_to_intent.items():
            if phrase in t_lower:
                return intent

        # 4. Default
        return "conversation"