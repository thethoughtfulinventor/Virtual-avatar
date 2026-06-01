from engine.intent_detector import IntentDetector
from engine.response_generator import ResponseGenerator
from engine.memory_retriever import MemoryRetriever
from engine.character_manager import CharacterManager
from engine.emotional_manager import EmotionalManager
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

        self.summarizer = Summarizer(self.llm_client)

        print("Brain initialized")

    def process(self, text):

        # Step 1: detect intent
        intent = (
            self.intent_detector.detect(text)
        )

        # Step 2: retrieve relevant memories
        memories = (
            self.memory_retriever.retrieve(text)
        )

        # Step 3: update emotional state
        self.emotional_manager.process(
            text,
            intent,
            self.character_manager
        )

        # Step 4: get dominant state and modifier
        dominant = (
            self.emotional_manager.get_dominant()
        )

        modifier = (
            self.character_manager
            .get_emotional_modifiers()
            .get(dominant, {})
        )

        # Step 5: get memory service
        memory = self.service_manager.get("memory")

        # Step 6: build system prompt from all layers
        system_prompt = (
            self.prompt_builder.build_system_prompt(
                self.character_manager,
                self.emotional_manager,
                memory
            )
        )

        # Step 7: build message history
        # (recent context + current user message)
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

        # Step 8: generate response via LLM
        response = self.llm_client.chat(
            system_prompt,
            messages
        )

        # Step 8b: extract and store any [REMEMBER:] facts
        response = self._extract_and_store_facts(
            response, memory
        )

        # Step 9: fallback if Ollama is offline
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

        # Step 10: store both sides of the turn
        memory.add_context("user", text)

        memory.add_context(
            "assistant",
            response,
            self.character_manager.get_name()
        )

        # Step 11: compress context if needed
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

        for match in re.findall(fact_pattern, response):

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

        # Check if compression threshold is reached
        entries = memory.recent_context.get_recent(25)

        if len(entries) < 25:
            return

        # Generate a meaningful summary via LLM
        summary = self.summarizer.summarize(entries)

        # Store and trim
        memory.compress_context(summary)

        if summary:
            print(f"[Memory] Episode stored: {summary[:60]}...")