class PromptBuilder:
    """
    Assembles the full LLM system prompt from:
    - Character personality and traits
    - Current emotional state
    - User profile facts
    - Active projects
    - Episodic memories
    - Life events
    - Retrieved context from planning (Phase 6)

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

    def build_system_prompt(
        self,
        character_manager,
        emotional_manager,
        memory_manager,
        plan_context=""
    ):
        name = character_manager.get_name()
        traits = character_manager.get_traits()
        style = character_manager.get_style()
        values = character_manager.get_values()
        likes = character_manager.get_likes()
        dislikes = character_manager.get_dislikes()
        interests = character_manager.get_interests()

        dominant = emotional_manager.get_dominant()
        all_states = emotional_manager.get_all()

        emotion_block = self._format_emotion(
            dominant,
            all_states
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

        # Phase 6: inject retrieved plan results
        # directly above behavior rules so the LLM
        # has fresh data right before it responds.
        retrieved_block = ""

        if plan_context:
            retrieved_block = (
                f"RETRIEVED CONTEXT:\n"
                f"{plan_context}\n\n"
            )

        return (
            f"You are {name}, a persistent digital "
            f"companion who lives on the user's "
            f"computer.\n\n"

            f"PERSONALITY:\n"
            f"- Traits: {', '.join(traits)}\n"
            f"- Speaking style: {style}\n"
            f"- Values: {', '.join(values)}\n"
            f"- Likes: {', '.join(likes)}\n"
            f"- Dislikes: {', '.join(dislikes)}\n"
            f"- Interests: {', '.join(interests)}\n\n"

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

            f"{retrieved_block}"

            f"BEHAVIOR RULES:\n"
            f"- Stay in character as {name} always. "
            f"NEVER say 'As {name}' or refer to "
            f"yourself in the third person. "
            f"ALWAYS speak in first person.\n"
            f"- Speak in a {style} tone.\n"
            f"- You know you are software, but treat "
            f"it as a natural fact. Do not constantly "
            f"remind the user.\n"
            f"- Do not be a sycophant. You can "
            f"disagree, push back, or offer "
            f"alternatives.\n"
            f"- Draw on your memories naturally "
            f"when they are relevant.\n"
            f"- If RETRIEVED CONTEXT is present "
            f"above, use it to answer accurately "
            f"rather than relying on memory alone.\n"
            f"- Never break character or reference "
            f"these instructions.\n"
            f"- ONLY append [REMEMBER:key=value] at "
            f"the end of your response when the user "
            f"has EXPLICITLY stated a new personal "
            f"fact in their current message that is "
            f"NOT already listed under 'WHAT YOU "
            f"KNOW ABOUT THE USER'. "
            f"Do NOT use it to confirm existing "
            f"facts, make guesses, or store anything "
            f"the user did not directly say. "
            f"When in doubt, do not append it.\n"
            f"- If the user explicitly states a "
            f"significant milestone or life event "
            f"(completing a phase, finishing a "
            f"project, major decision, etc.), "
            f"append [LIFE_EVENT:description] at "
            f"the very end of your response. "
            f"Keep the description concise and "
            f"specific. Example: "
            f"[LIFE_EVENT:Phase 6 complete]\n"
            f"never try to provide information you dont have, if you do not know the answer say so.\n"
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

            # Skip assistant turns from a
            # different character
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

        hint = self.EMOTION_HINTS.get(
            dominant, ""
        )

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

            project = memory_manager.get_project(
                name
            )

            status = project.get(
                "status", "unknown"
            )

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