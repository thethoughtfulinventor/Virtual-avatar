from engine.intent_detector import IntentDetector
from engine.response_generator import ResponseGenerator
from engine.memory_retriever import MemoryRetriever
from engine.character_manager import CharacterManager
from engine.emotional_manager import EmotionalManager
from engine.planner import Planner
from engine.plan_executor import PlanExecutor
from llm.summarizer import Summarizer
from llm.ollama_client import OllamaClient
from llm.prompt_builder import PromptBuilder
from llm.model_config import ModelConfig


class Brain:

    def __init__(
        self,
        state_manager,
        event_bus,
        service_manager
    ):

        self.state_manager = state_manager
        self.event_bus = event_bus
        self.service_manager = service_manager

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

        self.summarizer = Summarizer(
            self.llm_client
        )

        # Phase 6: Planning and Execution
        tool_registry = service_manager.get(
            "tool_registry"
        )

        if tool_registry is None:

            from engine.tool_registry import (
                ToolRegistry
            )

            tool_registry = ToolRegistry()

            print(
                "[Brain] No tool registry in "
                "service manager. "
                "Using empty registry."
            )

        self.planner = Planner(
            self.llm_client,
            tool_registry
        )

        self.executor = PlanExecutor(tool_registry)

        print("Brain initialized")

    def process(self, text):

        # Step 1: Detect intent
        intent = (
            self.intent_detector.detect(text)
        )

        # Step 2: Retrieve keyword memories
        memories = (
            self.memory_retriever.retrieve(text)
        )

        # Step 3: Update emotional state
        self.emotional_manager.process(
            text,
            intent,
            self.character_manager
        )

        # Step 4: Get dominant state and modifier
        dominant = (
            self.emotional_manager.get_dominant()
        )

        modifier = (
            self.character_manager
            .get_emotional_modifiers()
            .get(dominant, {})
        )

        # Step 5: Get memory service
        memory = self.service_manager.get("memory")

        # Step 6: Plan and execute
        #
        # For conversation-type messages the
        # Planner asks the LLM what steps are
        # needed. The Executor runs them and
        # returns the results as a context string
        # that gets injected into the response
        # prompt.
        #
        # Structured commands (memory_store,
        # project_create, etc.) are handled
        # directly by main.py routing and do
        # not need a planning pass.
        plan_context = ""

        if intent == "conversation":

            plan = self.planner.plan(
                text,
                memory,
                self.character_manager
            )

            plan_context = self.executor.execute(
                plan,
                memory
            )

        # Step 7: Build system prompt
        system_prompt = (
            self.prompt_builder.build_system_prompt(
                self.character_manager,
                self.emotional_manager,
                memory,
                plan_context=plan_context
            )
        )

        # Step 8: Build message history
        recent = memory.get_recent_context(
            ModelConfig.MAX_CONTEXT
        )

        messages = self.prompt_builder.format_context(
            recent,
            self.character_manager.get_name()
        )

        messages.append({
            "role": "user",
            "content": text
        })

        # Step 9: Generate response via LLM
        response = self.llm_client.chat(
            system_prompt,
            messages
        )

        # Step 9b: Extract and store inline facts
        response = self._extract_and_store_facts(
            response, memory
        )

        # Step 10: Fallback if Ollama is offline
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

        # Step 11: Store both sides of the turn
        memory.add_context("user", text)

        memory.add_context(
            "assistant",
            response,
            self.character_manager.get_name()
        )

        # Step 12: Compress context if needed
        self._compress_context(memory)

        return {
            "intent": intent,
            "response": response,
            "memories": memories,
            "emotional_state": dominant
        }

    def _extract_and_store_facts(
        self,
        response,
        memory
    ):
        import re

        # User profile facts
        fact_pattern = r'\[REMEMBER:([^\]]+)\]'

        for match in re.findall(
            fact_pattern, response
        ):

            if "=" in match:

                key, value = match.split("=", 1)
                key = key.strip()
                value = value.strip()

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

        for match in re.findall(
            event_pattern, response
        ):

            description = match.strip()

            if description:

                memory.add_life_event(description)

                print(
                    f"[Memory] Life event: "
                    f"{description}"
                )

        # Strip all tags from displayed response
        clean = re.sub(
            fact_pattern, "", response
        )

        clean = re.sub(
            event_pattern, "", clean
        ).strip()

        return clean

    def _compress_context(self, memory):

        entries = memory.recent_context.get_recent(
            25
        )

        if len(entries) < 25:
            return

        summary = self.summarizer.summarize(entries)

        memory.compress_context(summary)

        if summary:
            print(
                f"[Memory] Episode stored: "
                f"{summary[:60]}..."
            )