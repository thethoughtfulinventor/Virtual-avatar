from engine.intent_detector import IntentDetector
from engine.response_generator import ResponseGenerator
from engine.memory_retriever import MemoryRetriever
from engine.character_manager import CharacterManager
from engine.emotional_manager import EmotionalManager
from llm.summarizer import Summarizer
from llm.ollama_client import OllamaClient
from llm.prompt_builder import PromptBuilder
from engine.planner import Planner
from llm.model_config import ModelConfig


class Brain:

    def __init__(
        self,
        state_manager,
        event_bus,
        service_manager,
        roster
    ):

        self.state_manager = state_manager
        self.event_bus = event_bus
        self.service_manager = service_manager
        self.roster = roster

        self.intent_detector = IntentDetector()

        # Kept as fallback when LLM is offline
        self.response_generator = (
            ResponseGenerator()
        )

        memory = service_manager.get("memory")

        self.memory_retriever = (
            MemoryRetriever(memory)
        )

        self.character = state_manager.get(
            "active_character"
        )

        self.character_manager = CharacterManager(
            self.character
        )

        self.emotional_manager = EmotionalManager(
            self.character_manager.get_name()
        )

        self.llm_client = OllamaClient()

        self.prompt_builder = PromptBuilder()

        self.summarizer = Summarizer(self.llm_client)

        self.planner = Planner(
            self.llm_client,
            roster
        )

        print("Brain initialized")

    # --------------------------------------------------
    # Character switching
    # --------------------------------------------------

    def switch_character(self, name):
        """
        Switches the active character mid-session.

        Reinitializes CharacterManager and
        EmotionalManager for the new character.
        Shared memory is preserved.

        Returns the canonical character name on
        success, or None if not found.
        """

        canonical = self.roster.resolve_name(name)

        if not canonical:
            return None

        character_data = self.roster.get(canonical)

        if not character_data:
            return None

        self.state_manager.set(
            "active_character",
            character_data
        )

        self.character = character_data

        self.character_manager = CharacterManager(
            character_data
        )

        self.emotional_manager = EmotionalManager(
            self.character_manager.get_name()
        )

        print(
            f"[Brain] Character switched to {canonical}"
        )

        return canonical

    # --------------------------------------------------
    # Main processing loop
    # --------------------------------------------------

    def process(self, text):

        # Step 1: detect intent
        intent = (
            self.intent_detector.detect(text)
        )

        # Get memory service once — used throughout
        memory = self.service_manager.get("memory")

        # Step 2: handle explicit character switch
        # before any other processing
        if intent == "switch_character":
            return self._handle_switch(text, memory)

        # Step 3: retrieve relevant memories
        memories = (
            self.memory_retriever.retrieve(text)
        )

        # Step 4: run planner for conversation turns
        # Planner decides character routing and
        # response strategy. Skipped for system
        # commands to avoid extra LLM latency.
        plan = {
            "best_character": None,
            "reason": "",
            "response_strategy": "direct",
            "tools_needed": []
        }

        character_switched = False

        if (
            intent == "conversation"
            and ModelConfig.ENABLE_PLANNER
            and len(self.roster.get_names()) > 1
        ):

            recent_for_plan = (
                memory.get_recent_context(4)
            )

            plan = self.planner.plan(
                text,
                self.character_manager,
                recent_for_plan
            )

            # Auto-route to the recommended character
            # before generating the response
            if plan["best_character"]:

                canonical = self.switch_character(
                    plan["best_character"]
                )

                if canonical:
                    character_switched = True
                    print(
                        f"[Planner] Auto-routed to "
                        f"{canonical}: {plan['reason']}"
                    )

        # Step 5: update emotional state
        self.emotional_manager.process(
            text,
            intent,
            self.character_manager
        )

        # Step 6: get dominant state and modifier
        dominant = (
            self.emotional_manager.get_dominant()
        )

        modifier = (
            self.character_manager
            .get_emotional_modifiers()
            .get(dominant, {})
        )

        # Step 7: build system prompt from all layers
        system_prompt = (
            self.prompt_builder.build_system_prompt(
                self.character_manager,
                self.emotional_manager,
                memory,
                roster=self.roster,
                strategy=plan.get("response_strategy")
            )
        )

        # Step 8: build message history
        recent = memory.get_recent_context(
            ModelConfig.MAX_CONTEXT
        )

        messages = self.prompt_builder.format_context(
            recent,
            self.character_manager.get_name()
        )

        # When the planner auto-switched characters,
        # append a brief note so the new character
        # understands it was just routed in and
        # doesn't respond as if it needs to switch.
        user_content = text

        if character_switched:

            name = self.character_manager.get_name()

            user_content = (
                f"{text}\n"
                f"[You ({name}) were just routed into "
                f"this conversation to handle this "
                f"message. The switch has already "
                f"happened. Respond naturally.]"
            )

        messages.append({
            "role": "user",
            "content": user_content
        })

        # Step 9: generate LLM response
        response = self.llm_client.chat(
            system_prompt,
            messages
        )

        # Step 10: extract and store any facts/events
        response = self._extract_and_store_facts(
            response, memory
        )

        # Step 11: fallback if Ollama is offline
        if not response:

            print(
                "[Brain] LLM unavailable. "
                "Using template fallback."
            )

            response = (
                self.response_generator.generate(
                    intent,
                    text,
                    memories,
                    self.character_manager,
                    modifier
                )
            )

        # Step 12: store both sides of the turn
        memory.add_context("user", text)

        memory.add_context(
            "assistant",
            response,
            self.character_manager.get_name()
        )

        # Step 13: compress context if needed
        self._compress_context(memory)

        return {
            "intent": intent,
            "response": response,
            "memories": memories,
            "emotional_state": dominant,
            "character_switched": character_switched,
            "new_character": (
                self.character_manager.get_name()
                if character_switched
                else None
            )
        }

    # --------------------------------------------------
    # Internal helpers
    # --------------------------------------------------

    def _handle_switch(self, text, memory):
        """
        Handles an explicit 'switch character' or
        'switch to' command from the user.

        Switches the character, then has the new
        character respond to the switch request.
        """

        text_lower = text.lower().strip()

        name = (
            text_lower
            .replace("switch character ", "")
            .replace("switch to ", "")
            .strip()
        )

        old_name = self.character_manager.get_name()

        canonical = self.switch_character(name)

        if not canonical:

            available = ", ".join(
                self.roster.get_names()
            )

            response = (
                f"No character named '{name}' found. "
                f"Available: {available}"
            )

            return {
                "intent": "switch_character",
                "response": response,
                "memories": [],
                "emotional_state": (
                    self.emotional_manager.get_dominant()
                ),
                "character_switched": False,
                "new_character": None
            }

        # Have the new character acknowledge
        # the switch naturally
        system_prompt = (
            self.prompt_builder.build_system_prompt(
                self.character_manager,
                self.emotional_manager,
                memory,
                roster=self.roster
            )
        )

        recent = memory.get_recent_context(
            ModelConfig.MAX_CONTEXT
        )

        messages = self.prompt_builder.format_context(
            recent,
            canonical
        )

        # The new character sees the switch request
        messages.append({
            "role": "user",
            "content": text
        })

        response = self.llm_client.chat(
            system_prompt,
            messages
        )

        response = self._extract_and_store_facts(
            response, memory
        )

        if not response:
            response = f"{canonical} online."

        memory.add_context("user", text)
        memory.add_context(
            "assistant",
            response,
            canonical
        )

        return {
            "intent": "switch_character",
            "response": response,
            "memories": [],
            "emotional_state": (
                self.emotional_manager.get_dominant()
            ),
            "character_switched": True,
            "new_character": canonical
        }

    def _extract_and_store_facts(
        self,
        response,
        memory
    ):
        import re

        if not response:
            return response

        # User profile facts
        fact_pattern = r'\[REMEMBER:([^\]]+)\]'

        # Keys containing these words are almost
        # never legitimate user profile facts.
        # They indicate the LLM tagging its own
        # internal state or conversation metadata.
        key_blacklist = [
            "switch", "request", "wants", "asked",
            "said", "current", "active", "character",
            "action", "command", "message", "response",
            "user_request", "context", "intent"
        ]

        for match in re.findall(fact_pattern, response):

            if "=" in match:

                key, value = match.split("=", 1)
                key = key.strip()
                value = value.strip()
                key_lower = key.lower()

                # Reject metadata keys
                if any(
                    bad in key_lower
                    for bad in key_blacklist
                ):
                    print(
                        f"[Memory] Rejected tag: "
                        f"{key} = {value}"
                    )
                    continue

                # Reject bare booleans —
                # real user facts have actual values
                if value.lower() in ("true", "false"):
                    print(
                        f"[Memory] Rejected tag "
                        f"(boolean value): {key}"
                    )
                    continue

                existing = memory.recall(key)

                if existing == value:
                    continue

                memory.remember(key, value)

                print(
                    f"[Memory] Stored: "
                    f"{key} = {value}"
                )

        # Life events
        event_pattern = r'\[LIFE_EVENT:([^\]]+)\]'

        for match in re.findall(event_pattern, response):

            description = match.strip()

            if description:

                memory.add_life_event(description)

                print(
                    f"[Memory] Life event: {description}"
                )

        # Strip all tags from displayed response
        clean = re.sub(fact_pattern, "", response)
        clean = re.sub(event_pattern, "", clean).strip()

        return clean

    def _compress_context(self, memory):

        entries = memory.recent_context.get_recent(25)

        if len(entries) < 25:
            return

        summary = self.summarizer.summarize(entries)

        memory.compress_context(summary)

        if summary:
            print(
                f"[Memory] Episode stored: "
                f"{summary[:60]}..."
            )