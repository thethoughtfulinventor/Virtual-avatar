from conversation.intent_detector import IntentDetector
from conversation.fallback_response_generator import ResponseGenerator
from memory.memory_retriever import MemoryRetriever
from characters.character_manager import CharacterManager
from emotion.emotional_manager import EmotionalManager
from skills.tool_registry import ToolRegistry
from planning.plan_executor import PlanExecutor
from planning.plan import Plan, PlanStep
from llm.summarizer import Summarizer
from llm.ollama_client import OllamaClient
from llm.prompt_builder import PromptBuilder
from planning.planner import Planner
from llm.model_config import ModelConfig
from conversation.response_processor import ResponseProcessor
from characters.character_router import CharacterRouter

# Intents that are pure system commands —
# no LLM call needed, no context added.
_SYSTEM_INTENTS = frozenset({
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
})

class Brain:

    def __init__(
        self,
        state_manager,
        event_bus,
        service_manager,
        roster,
    ):
        self.state_manager   = state_manager
        self.event_bus       = event_bus
        self.service_manager = service_manager
        self.roster          = roster

        self.intent_detector    = IntentDetector()
        self.response_generator = ResponseGenerator()

        memory = service_manager.get("memory")

        self.memory_retriever = MemoryRetriever(memory)

        self.character = state_manager.get("active_character")
        self.character_manager = CharacterManager(self.character)

        self.emotional_manager = EmotionalManager(
            self.character_manager.get_name()
        )

        self.llm_client    = OllamaClient()
        self.prompt_builder = PromptBuilder()
        self.summarizer    = Summarizer(self.llm_client)
        self.tool_registry = ToolRegistry()
        self.plan_executor = PlanExecutor(self.tool_registry)

        self.response_processor = ResponseProcessor(self.tool_registry)

        self.character_router = CharacterRouter(
            roster=roster,
            state_manager=state_manager,
            prompt_builder=self.prompt_builder,
            llm_client=self.llm_client,
            tool_registry=self.tool_registry
        )


        self.planner = Planner(
            self.llm_client,
            roster,
            self.tool_registry,
        )

        print("Brain initialized")

    # --------------------------------------------------
    # Main processing loop
    # --------------------------------------------------

    def process(self, text: str) -> dict:
        intent = self.intent_detector.detect(text)
        memory = self.service_manager.get("memory")

        if intent == "switch_character":
            result = self.character_router._handle_switch(text, memory)
            if result.get("character_switched"):
                self.character_manager = self.character_router.character_manager
                self.emotional_manager = self.character_router.emotional_manager
            return result   

        if intent in _SYSTEM_INTENTS:
            return {
                "intent":            intent,
                "response":          "",
                "memories":          [],
                "emotional_state":   self.emotional_manager.get_dominant(),
                "character_switched": False,
                "new_character":     None,
            }

        memories = self.memory_retriever.retrieve(text)

        plan = {
            "best_character":    None,
            "reason":            "",
            "response_strategy": "direct",
            "tools_needed":      [],
        }

        character_switched = False

        if intent == "conversation" and ModelConfig.ENABLE_PLANNER:
            recent_for_plan = memory.get_recent_context(4)
            plan = self.planner.plan(
                text, self.character_manager, recent_for_plan
            )

            if plan["best_character"]:
                canonical = self.character_router.switch_character(plan["best_character"])   
                if canonical:
                    character_switched = True
                    # ✅ SYNC: Update Brain's managers here too
                    self.character_manager = self.character_router.character_manager
                    self.emotional_manager = self.character_router.emotional_manager
                    
                    print(f"[Planner] Auto-routed to {canonical}: {plan['reason']}")

        # Execute planner-requested tools
        retrieved_context = ""
        if plan.get("tools_needed"):
            retrieved_context = self._execute_tools(
                plan["tools_needed"], memory
            )

        # Emotional processing
        self.emotional_manager.process(
            text, intent, self.character_manager
        )
        dominant = self.emotional_manager.get_dominant()
        modifier = (
            self.character_manager
            .get_emotional_modifiers()
            .get(dominant, {})
        )

        # Build system prompt
        system_prompt = self.prompt_builder.build_system_prompt(
            self.character_manager,
            self.emotional_manager,
            memory,
            roster=self.roster,
            strategy=plan.get("response_strategy"),
        )

        if retrieved_context:
            system_prompt += (
                f"\n\nRETRIEVED CONTEXT:\n{retrieved_context}"
            )

        recent = memory.get_recent_context(ModelConfig.MAX_CONTEXT)
        messages = self.prompt_builder.format_context(
            recent, self.character_manager.get_name()
        )

        user_content = text
        if character_switched:
            name = self.character_manager.get_name()
            user_content = (
                f"{text}\n"
                f"[You ({name}) were just routed into "
                f"this conversation. The switch has already "
                f"happened. Respond naturally.]"
            )

        messages.append({"role": "user", "content": user_content})

        response = self.llm_client.chat(
            system_prompt,
            messages
        )

        if response:
            response = self.response_processor.process(
                response,
                memory
            )

        # Fallback if LLM unavailable or returned nothing
        if not response:
            print("[Brain] LLM unavailable. Using template fallback.")
            response = self.response_generator.generate(
                intent, text, memories,
                self.character_manager, modifier,
            )

        memory.add_context("user", text)
        memory.add_context(
            "assistant", response, self.character_manager.get_name()
        )

        self._compress_context(memory)

        return {
            "intent":            intent,
            "response":          response,
            "memories":          memories,
            "emotional_state":   dominant,
            "character_switched": character_switched,
            "new_character": (
                self.character_manager.get_name()
                if character_switched else None
            ),
        }

    # --------------------------------------------------
    # Internal helpers
    # --------------------------------------------------

    def _execute_tools(self, tools_needed: list, memory) -> str:
        """Build and run an execution plan from the planner's tool list."""
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
                    description=tool_call.get("description", tool_name),
                )
            )

        execution_plan.steps.append(PlanStep(tool="respond"))
        return self.plan_executor.execute(execution_plan, memory)


    def _compress_context(self, memory) -> None:
        """
        If context has grown past 25 entries, summarise it
        into an episode and trim to the last 3 turns.
        """
        if memory.recent_context.count() < 25:
            return

        entries = memory.recent_context.get_recent(25)
        summary = self.summarizer.summarize(entries)
        memory.compress_context(summary)

        if summary:
            print(f"[Memory] Episode stored: {summary[:60]}...")