from engine.intent_detector import IntentDetector
from engine.response_generator import ResponseGenerator
from engine.memory_retriever import MemoryRetriever
from engine.character_manager import CharacterManager
from engine.emotional_manager import EmotionalManager
from engine.tool_registry import ToolRegistry
from engine.plan_executor import PlanExecutor
from engine.plan import Plan, PlanStep
from llm.summarizer import Summarizer
from llm.ollama_client import OllamaClient
from llm.prompt_builder import PromptBuilder
from engine.planner import Planner
from llm.model_config import ModelConfig


# Intents that are pure system commands —
# no LLM call needed, no context added.
# main.py handles the action after process() returns.
_SYSTEM_INTENTS = {
    "context_clear",
    "context_view",
    "episode_clear",
    "episode_list",
    "episode_create",
    "projects_list",
    "project_create",
    "project_lookup",
    "life_events_list",
    "life_event_create",
    "state_view",
    "memory_store",
    "memory_recall",
}


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

        self.tool_registry = ToolRegistry()

        self.plan_executor = PlanExecutor(
            self.tool_registry
        )

        self.planner = Planner(
            self.llm_client,
            roster,
            self.tool_registry
        )

        print("Brain initialized")

    # --------------------------------------------------
    # Character switching
    # --------------------------------------------------

    def switch_character(self, name):

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

        intent = (
            self.intent_detector.detect(text)
        )

        memory = self.service_manager.get("memory")

        # Route character switches immediately
        if intent == "switch_character":
            return self._handle_switch(text, memory)

        # System commands: skip LLM entirely.
        # These are instant storage/retrieval ops
        # handled by main.py after we return.
        # Bypassing the LLM for these saves a full
        # round-trip per command (5–30 s on local models).
        if intent in _SYSTEM_INTENTS:
            return {
                "intent": intent,
                "response": "",
                "memories": [],
                "emotional_state": (
                    self.emotional_manager.get_dominant()
                ),
                "character_switched": False,
                "new_character": None
            }

        memories = (
            self.memory_retriever.retrieve(text)
        )

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
        ):

            recent_for_plan = (
                memory.get_recent_context(4)
            )

            plan = self.planner.plan(
                text,
                self.character_manager,
                recent_for_plan
            )

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

        # Execute any tools the planner requested
        retrieved_context = ""

        if plan.get("tools_needed"):

            retrieved_context = self._execute_tools(
                plan["tools_needed"], memory
            )

        # Emotional state
        self.emotional_manager.process(
            text, intent, self.character_manager
        )

        dominant = (
            self.emotional_manager.get_dominant()
        )

        modifier = (
            self.character_manager
            .get_emotional_modifiers()
            .get(dominant, {})
        )

        # Build system prompt
        system_prompt = (
            self.prompt_builder.build_system_prompt(
                self.character_manager,
                self.emotional_manager,
                memory,
                roster=self.roster,
                strategy=plan.get("response_strategy")
            )
        )

        if retrieved_context:
            system_prompt += (
                f"\n\nRETRIEVED CONTEXT:\n"
                f"{retrieved_context}"
            )

        recent = memory.get_recent_context(
            ModelConfig.MAX_CONTEXT
        )

        messages = self.prompt_builder.format_context(
            recent,
            self.character_manager.get_name()
        )

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

        response = self.llm_client.chat(
            system_prompt, messages
        )

        # Extract facts and response actions once each
        # (previously called _extract_and_store_facts twice)
        response = self._extract_and_store_facts(
            response, memory
        )
        response = self._extract_response_actions(
            response, memory
        )

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

        memory.add_context("user", text)

        memory.add_context(
            "assistant",
            response,
            self.character_manager.get_name()
        )

        self._compress_context(memory)

        return {
            "intent": intent,
            "response": response,
            "memories": memories,
            "emotional_state": dominant,
            "character_switched": character_switched,
            "new_character": (
                self.character_manager.get_name()
                if character_switched else None
            )
        }

    # --------------------------------------------------
    # Internal helpers
    # --------------------------------------------------

    def _execute_tools(self, tools_needed, memory):

        if not tools_needed:
            return ""

        execution_plan = Plan(goal="tool_execution")

        for tool_call in tools_needed:

            if not isinstance(tool_call, dict):
                continue

            tool_name = tool_call.get("tool", "")

            if not tool_name or tool_name == "respond":
                continue

            execution_plan.steps.append(
                PlanStep(
                    tool=tool_name,
                    args=tool_call.get("args", {}),
                    description=tool_call.get(
                        "description", tool_name
                    )
                )
            )

        execution_plan.steps.append(
            PlanStep(tool="respond")
        )

        return self.plan_executor.execute(
            execution_plan, memory
        )

    def _handle_switch(self, text, memory):

        text_lower = text.lower().strip()

        name = (
            text_lower
            .replace("switch character ", "")
            .replace("switch to ", "")
            .strip()
        )

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

        messages.append({
            "role": "user",
            "content": (
                f"{text}\n"
                f"[You ({canonical}) just took over. "
                f"Respond ONLY to this current message. "
                f"Do not revisit or answer earlier "
                f"questions from the conversation history.]"
            )
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
            "assistant", response, canonical
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
        self, response, memory
    ):
        import re

        if not response:
            return response

        fact_pattern = r'\[REMEMBER:([^\]]+)\]'

        key_blacklist = [
            "switch", "request", "wants", "asked",
            "said", "current", "active", "character",
            "action", "command", "message", "response",
            "user_request", "context", "intent",
            "search", "result", "file", "path", "folder",
            "directory", "system", "cpu", "ram", "gpu",
            "storage", "terminal", "process", "output",
            "error", "tool", "skill", "retrieved",
            "news", "weather", "data", "query",
        ]

        for match in re.findall(fact_pattern, response):

            if "=" in match:

                key, value = match.split("=", 1)
                key = key.strip()
                value = value.strip()
                key_lower = key.lower()

                if any(
                    bad in key_lower
                    for bad in key_blacklist
                ):
                    print(
                        f"[Memory] Rejected tag: "
                        f"{key} = {value}"
                    )
                    continue

                if value.lower() in ("true", "false"):
                    print(
                        f"[Memory] Rejected tag "
                        f"(boolean): {key}"
                    )
                    continue

                existing = memory.recall(key)

                if existing == value:
                    continue

                memory.remember(key, value)

                print(f"[Memory] Stored: {key} = {value}")

        event_pattern = r'\[LIFE_EVENT:([^\]]+)\]'

        for match in re.findall(event_pattern, response):

            description = match.strip()

            if description:

                memory.add_life_event(description)

                print(
                    f"[Memory] Life event: {description}"
                )

        clean = re.sub(fact_pattern, "", response)
        clean = re.sub(event_pattern, "", clean).strip()

        return clean

    def _compress_context(self, memory):

        if memory.recent_context.count() < 25:
            return

        entries = memory.recent_context.get_recent(25)
        summary = self.summarizer.summarize(entries)
        memory.compress_context(summary)

        if summary:
            print(
                f"[Memory] Episode stored: "
                f"{summary[:60]}..."
            )

    def _extract_response_actions(
        self, response, memory
    ):
        import re

        if not response:
            return response

        write_pattern = (
            r'\[WRITE_FILE:([^\]]+)\]'
            r'(.*?)'
            r'\[/WRITE_FILE\]'
        )

        for match in re.finditer(
            write_pattern, response, re.DOTALL
        ):
            path = match.group(1).strip()
            content = match.group(2)

            write_tool = self.tool_registry.get(
                "file_write"
            )

            if write_tool:
                result = write_tool.run(
                    {"path": path, "content": content},
                    {"memory": memory}
                )
                print(f"[FileWrite] {result}")

            else:
                print(
                    f"[FileWrite] Tool not registered."
                )

        return re.sub(
            write_pattern, "", response, flags=re.DOTALL
        ).strip()