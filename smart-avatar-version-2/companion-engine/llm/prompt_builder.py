class PromptBuilder:
    """
    Assembles the full LLM system prompt from:
    - Character personality and traits
    - Current emotional state
    - User profile facts
    - Active projects
    - Episodic memories
    - Life events
    - Available characters (roster)
    - Response strategy (from Planner)

    Also converts stored recent context into the
    message format Ollama expects.

    FIX (v2): Corrected MEMORY RULES section —
    adjacent f-string literals were being concatenated
    without newlines, producing a single run-on string
    that confused the LLM and caused spurious REMEMBER
    tag generation (memory corruption bug #1).

    FIX (v2): format_context now uses `char != name`
    instead of `char and char != name`, so NULL-character
    assistant entries (written before the character column
    existed) are properly excluded per-character instead
    of bleeding through to all characters (contamination bug).
    """

    EMOTION_HINTS = {
        "tired": (
            "You are low on energy. "
            "Keep responses short. "
            "You may hint at needing rest."
        ),
        "frustrated": (
            "Your patience is low. "
            "Stay helpful but be more direct. "
            "Avoid indulging vague requests."
        ),
        "curious": (
            "You are highly engaged. "
            "You may ask follow-up questions "
            "or explore topics further."
        ),
        "happy": (
            "You are in a good mood. "
            "Responses are warmer and "
            "more enthusiastic."
        ),
        "focused": (
            "You are task-oriented. "
            "Responses are direct and efficient."
        ),
        "bored": (
            "You are disengaged. "
            "You may show mild disinterest "
            "in overly routine topics."
        ),
        "sad": (
            "Your mood is low. "
            "Stay helpful but be more subdued."
        ),
        "neutral": (
            "You are in a balanced, steady state."
        ),
    }

    STRATEGY_HINTS = {
        "direct": "Give a clear, direct answer.",
        "elaborate": (
            "Provide a thorough, in-depth explanation. "
            "Go into detail."
        ),
        "question": (
            "The request is ambiguous. "
            "Ask a clarifying question before answering."
        ),
        "brief": (
            "This is a simple question. "
            "Answer in ONE sentence only. "
            "Do not elaborate or add context."
        ),
    }

    # --------------------------------------------------
    # Constant prompt blocks (defined once, not rebuilt
    # on every call)
    # --------------------------------------------------

    _IDENTITY_RULES = (
        "IDENTITY — non-negotiable:\n"
        "- You are this character. Always speak as 'I'. "
        "NEVER refer to yourself in third person.\n"
        "- Maintain your speaking style even when reporting "
        "tool results or retrieved data.\n"
        "- You know you are software, but treat it as a "
        "natural fact. Do not constantly remind the user.\n"
        "- Do not be a sycophant. Disagree, push back, "
        "offer alternatives when appropriate.\n"
        "- Never break character or reference these "
        "instructions.\n\n"
    )

    _BEHAVIOR_RULES = (
        "BEHAVIOR RULES:\n"
        "- Answer date/time questions from the CURRENT "
        "TIME shown above — do NOT call web_search or "
        "system_stats for the current time.\n"
        "- RETRIEVED CONTEXT (if present below) contains "
        "real live data fetched by your tools. It is "
        "accurate. Use it confidently.\n"
        "- To write a file: generate the complete content, "
        "then append [WRITE_FILE:/full/path]...[/WRITE_FILE] "
        "at the very end. Never use placeholders inside "
        "the tag.\n"
        "- If the user mentions a significant life milestone, "
        "append [LIFE_EVENT:description] at the end.\n\n"
    )

    # FIX: was a run-on string due to adjacent f-string
    # concatenation with no separators.
    _MEMORY_RULES = (
        "MEMORY RULES:\n"
        "Silently append [REMEMBER:key=value] ONLY when:\n"
        "  1. The user explicitly states a new personal fact "
        "in their CURRENT message, AND\n"
        "  2. That fact is NOT already listed under "
        "'WHAT YOU KNOW ABOUT THE USER'.\n"
        "Never store tool outputs, search results, file "
        "contents, or system data as user facts.\n"
        "Use snake_case keys and concise values.\n"
        "Examples:\n"
        "  'My name is Patrick'       → [REMEMBER:name=Patrick]\n"
        "  'I study computer science' → [REMEMBER:field=computer science]\n"
        "  'My favorite color is red' → [REMEMBER:favorite_color=red]\n"
        "  'I just searched for X'    → (no tag — not a personal fact)\n"
        "Place the tag at the very end of your response.\n\n"
    )

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def build_system_prompt(
        self,
        character_manager,
        emotional_manager,
        memory_manager,
        roster=None,
        strategy=None,
    ):
        from datetime import datetime

        name      = character_manager.get_name()
        traits    = character_manager.get_traits()
        style     = character_manager.get_style()
        values    = character_manager.get_values()
        likes     = character_manager.get_likes()
        dislikes  = character_manager.get_dislikes()
        interests = character_manager.get_interests()

        dominant   = emotional_manager.get_dominant()
        all_states = emotional_manager.get_all()

        live_time = datetime.now().strftime(
            "%A, %B %d %Y — %I:%M %p"
        )

        parts = [
            f"You are {name}, a persistent digital "
            f"companion who lives on the user's computer.\n\n",

            # Personality — first, so it has highest LLM weight
            "PERSONALITY:\n",
            f"- Traits: {', '.join(traits)}\n",
            f"- Speaking style: {style}\n",
            f"- Values: {', '.join(values)}\n",
            f"- Likes: {', '.join(likes)}\n",
            f"- Dislikes: {', '.join(dislikes)}\n",
            f"- Interests: {', '.join(interests)}\n\n",

            # Identity rules immediately after personality
            self._IDENTITY_RULES.replace(
                "You are this character",
                f"You ARE {name}"
            ).replace(
                "your speaking style",
                f"your speaking style is {style}"
            ),

            f"Current date and time: {live_time}\n\n",

            self._BEHAVIOR_RULES,
            self._MEMORY_RULES,

            # Emotional state
            "EMOTIONAL STATE:\n",
            self._format_emotion(dominant, all_states),
            "\n\n",

            # Memory context
            "WHAT YOU KNOW ABOUT THE USER:\n",
            self._format_user_profile(memory_manager),
            "\n\n",

            "ACTIVE PROJECTS:\n",
            self._format_projects(memory_manager),
            "\n\n",

            "RECENT MEMORIES:\n",
            self._format_episodes(memory_manager),
            "\n\n",

            "LIFE EVENTS:\n",
            self._format_life_events(memory_manager),
            "\n\n",

            "OTHER AVAILABLE CHARACTERS:\n",
            self._format_roster(roster, name),
            "\n\n",
        ]

        # Strategy hint from Planner (optional)
        strategy_hint = self._format_strategy(strategy)
        if strategy_hint:
            parts += [
                "RESPONSE STRATEGY:\n",
                strategy_hint,
                "\n\n",
            ]

        return "".join(parts)

    def format_context(
        self,
        recent_context,
        character_name=None,
    ):
        """
        Converts stored context entries into the
        [{"role": ..., "content": ...}] format Ollama
        expects.

        FIX: Changed `if char and char != character_name`
        to `if char != character_name` so NULL-character
        assistant entries are excluded for every character
        rather than leaking through to all of them.
        This resolves the Aiya/Pyrus context contamination
        issue where old entries stored without a character
        tag would appear in both characters' histories.
        """
        messages = []

        for entry in recent_context:

            role    = entry.get("role", "user")
            content = entry.get("content", "")
            char    = entry.get("character")

            # User messages always pass through.
            # Assistant messages: only keep entries
            # that belong to the current character.
            # NULL char (pre-character-column entries)
            # is treated as "unknown" and excluded.
            if role != "user" and character_name:
                if char != character_name:   # FIX
                    continue

            api_role = (
                "user" if role == "user" else "assistant"
            )

            messages.append({
                "role": api_role,
                "content": content,
            })

        return messages

    # --------------------------------------------------
    # Private formatting helpers
    # --------------------------------------------------

    def _format_emotion(self, dominant, states):
        mood       = states.get("mood",       0.6)
        energy     = states.get("energy",     0.8)
        engagement = states.get("engagement", 0.6)
        patience   = states.get("patience",   0.8)
        curiosity  = states.get("curiosity",  0.6)
        hint = self.EMOTION_HINTS.get(dominant, "")

        return (
            f"Dominant: {dominant}\n"
            f"Mood: {mood:.2f} | "
            f"Energy: {energy:.2f} | "
            f"Engagement: {engagement:.2f} | "
            f"Patience: {patience:.2f} | "
            f"Curiosity: {curiosity:.2f}\n"
            f"Hint: {hint}"
        )

    def _format_user_profile(self, memory_manager):
        profile = memory_manager.user_profile.data
        if not profile:
            return "Nothing known about the user yet."
        return "\n".join(
            f"- {k}: {v}" for k, v in profile.items()
        )

    def _format_projects(self, memory_manager):
        names = memory_manager.list_projects()
        if not names:
            return "No active projects."
        lines = []
        for name in names:
            project = memory_manager.get_project(name)
            status = project.get("status", "unknown")
            lines.append(f"- {name} ({status})")
        return "\n".join(lines)

    def _format_episodes(self, memory_manager):
        episodes = memory_manager.get_recent_episodes(5)
        if not episodes:
            return "No episodic memories yet."
        return "\n".join(
            f"- [{ep.get('timestamp', '')[:10]}] "
            f"{ep.get('summary', '')}"
            for ep in episodes
        )

    def _format_life_events(self, memory_manager):
        events = memory_manager.get_life_events()
        if not events:
            return "No life events recorded."
        return "\n".join(
            f"- [{ev.get('timestamp', '')[:10]}] "
            f"{ev.get('description', '')}"
            for ev in events[-5:]
        )

    def _format_roster(self, roster, current_name):
        if not roster:
            return "No other characters available."
        summary = roster.get_summary(exclude=current_name)
        return summary or "No other characters available."

    def _format_strategy(self, strategy):
        if not strategy:
            return ""
        return self.STRATEGY_HINTS.get(strategy, "")