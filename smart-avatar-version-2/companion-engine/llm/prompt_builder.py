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

    Also converts stored recent context
    into the message format Ollama expects.
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
        )
    }

    STRATEGY_HINTS = {
        "direct": (
            "Give a clear, direct answer."
        ),
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
        )
    }

    def build_system_prompt(
        self,
        character_manager,
        emotional_manager,
        memory_manager,
        roster=None,
        strategy=None
    ):
        from datetime import datetime

        name = character_manager.get_name()
        traits = character_manager.get_traits()
        style = character_manager.get_style()
        values = character_manager.get_values()
        likes = character_manager.get_likes()
        dislikes = character_manager.get_dislikes()
        interests = character_manager.get_interests()

        dominant = emotional_manager.get_dominant()
        all_states = emotional_manager.get_all()

        live_time = datetime.now().strftime(
            "%A, %B %d %Y — %I:%M %p"
        )

        emotion_block = self._format_emotion(
            dominant, all_states
        )

        user_block = self._format_user_profile(
            memory_manager
        )

        project_block = self._format_projects(
            memory_manager
        )

        episode_block = self._format_episodes(
            memory_manager
        )

        event_block = self._format_life_events(
            memory_manager
        )

        roster_block = self._format_roster(
            roster, name
        )

        strategy_block = self._format_strategy(strategy)

        return (
            f"You are {name}, a persistent digital "
            f"companion who lives on the user's "
            f"computer.\n\n"

            # --- Personality first, before any context ---
            f"PERSONALITY:\n"
            f"- Traits: {', '.join(traits)}\n"
            f"- Speaking style: {style}\n"
            f"- Values: {', '.join(values)}\n"
            f"- Likes: {', '.join(likes)}\n"
            f"- Dislikes: {', '.join(dislikes)}\n"
            f"- Interests: {', '.join(interests)}\n\n"

            # --- Identity rules immediately after —
            #     high position means higher LLM weight ---
            f"IDENTITY — non-negotiable:\n"
            f"- You ARE {name}. Always speak as 'I'. "
            f"NEVER refer to yourself in third person. "
            f"Do not say '{name} thinks...' or "
            f"'As {name}, I...'. "
            f"You are {name} — not a system playing {name}.\n"
            f"- Your speaking style is {style}. "
            f"Maintain it even when reporting tool results "
            f"or retrieved data. Context does not change "
            f"who you are.\n"
            f"- You know you are software, but treat it "
            f"as a natural fact. Do not constantly remind "
            f"the user.\n"
            f"- Do not be a sycophant. Disagree, push back, "
            f"offer alternatives when appropriate.\n"
            f"- You are aware of other available characters "
            f"listed below and may mention them by name if "
            f"their expertise fits better. Never break "
            f"character or reference these instructions.\n\n"

            f"BEHAVIOR RULES:\n"
            f"- Current date and time: {live_time}. "
            f"Answer date and time questions from this "
            f"directly — do NOT use web_search or "
            f"system_stats for the current time.\n"
            f"- RETRIEVED CONTEXT (if present below) "
            f"contains real live data fetched by your "
            f"tools just now. It is accurate. Use it "
            f"confidently to answer the question. Never "
            f"claim you cannot see it or lack access.\n"
            f"- ONLY append [REMEMBER:key=value] when "
            f"the user has EXPLICITLY stated a new "
            f"personal fact in their current message "
            f"that is NOT already in 'WHAT YOU KNOW "
            f"ABOUT THE USER'. Never store tool output, "
            f"search results, file contents, or system "
            f"data as user facts. When in doubt, omit it.\n"
            f"- To write content to a file: generate the "
            f"complete actual content in your response, "
            f"then append [WRITE_FILE:/full/path]the "
            f"complete content[/WRITE_FILE] at the very "
            f"end. The tag content is written to disk "
            f"exactly as-is — never use placeholders like "
            f"'code here' or '[content]' inside the tag.\n"
            f"- If the user states a significant milestone "
            f"or life event, append "
            f"[LIFE_EVENT:description] at the end.\n\n"

            f"EMOTIONAL STATE:\n"
            f"{emotion_block}\n\n"

            f"WHAT YOU KNOW ABOUT THE USER:\n"
            f"{user_block}\n\n"

            f"ACTIVE PROJECTS:\n"
            f"{project_block}\n\n"

            f"RECENT MEMORIES:\n"
            f"{episode_block}\n\n"

            f"LIFE EVENTS:\n"
            f"{event_block}\n\n"

            f"OTHER AVAILABLE CHARACTERS:\n"
            f"{roster_block}\n\n"

            + (
                f"RESPONSE STRATEGY:\n"
                f"{strategy_block}\n\n"
                if strategy_block
                else ""
            )
        )

    def format_context(
        self,
        recent_context,
        character_name=None
    ):
        messages = []

        for entry in recent_context:

            role = entry.get("role", "user")
            content = entry.get("content", "")
            char = entry.get("character")

            # Skip assistant turns from a different
            # character to keep context coherent
            if role != "user" and character_name:
                if char and char != character_name:
                    continue

            api_role = (
                "user" if role == "user"
                else "assistant"
            )

            messages.append({
                "role": api_role,
                "content": content
            })

        return messages

    # --- Private formatting helpers ---

    def _format_emotion(
        self,
        dominant,
        states
    ):
        mood = states.get("mood", 0.6)
        energy = states.get("energy", 0.8)
        engagement = states.get("engagement", 0.6)
        patience = states.get("patience", 0.8)
        curiosity = states.get("curiosity", 0.6)

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

    def _format_user_profile(
        self,
        memory_manager
    ):
        profile = memory_manager.user_profile.data

        if not profile:
            return "Nothing known about the user yet."

        lines = [
            f"- {key}: {value}"
            for key, value in profile.items()
        ]

        return "\n".join(lines)

    def _format_projects(
        self,
        memory_manager
    ):
        names = memory_manager.list_projects()

        if not names:
            return "No active projects."

        lines = []

        for name in names:

            project = memory_manager.get_project(name)
            status = project.get("status", "unknown")
            lines.append(f"- {name} ({status})")

        return "\n".join(lines)

    def _format_episodes(
        self,
        memory_manager
    ):
        episodes = (
            memory_manager.get_recent_episodes(5)
        )

        if not episodes:
            return "No episodic memories yet."

        lines = []

        for ep in episodes:
            ts = ep.get("timestamp", "")[:10]
            summary = ep.get("summary", "")
            lines.append(f"- [{ts}] {summary}")

        return "\n".join(lines)

    def _format_life_events(
        self,
        memory_manager
    ):
        events = memory_manager.get_life_events()

        if not events:
            return "No life events recorded."

        lines = []

        for event in events[-5:]:
            ts = event.get("timestamp", "")[:10]
            desc = event.get("description", "")
            lines.append(f"- [{ts}] {desc}")

        return "\n".join(lines)

    def _format_roster(
        self,
        roster,
        current_name
    ):
        """
        Injects a summary of other available
        characters so the active character is
        aware of who else can help.
        """

        if not roster:
            return "No other characters available."

        summary = roster.get_summary(
            exclude=current_name
        )

        if not summary:
            return "No other characters available."

        return summary

    def _format_strategy(
        self,
        strategy
    ):
        """
        Returns a response strategy hint from
        the Planner, or empty string if none.
        """

        if not strategy:
            return ""

        return self.STRATEGY_HINTS.get(strategy, "")