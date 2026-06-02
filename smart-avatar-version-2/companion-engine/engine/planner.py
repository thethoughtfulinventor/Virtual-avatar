import json
import re

from engine.plan import Plan, PlanStep


class Planner:
    """
    Phase 6: Planning layer.

    The Planner uses the LLM to decide what
    to do before the response is generated.

    Given the user's message and a list of
    available tools, it outputs a structured
    JSON plan. The PlanExecutor then runs
    each step and collects the results, which
    are injected into the system prompt so
    the LLM can answer with real data in hand.

    This separates thinking from action:

        User message
            → Planner (LLM pass 1 — what to do)
            → PlanExecutor (run the steps)
            → Brain (LLM pass 2 — respond)
    """

    SYSTEM = (
        "You are the planning module for a "
        "digital companion. Given a user message "
        "and a list of available tools, output a "
        "JSON execution plan.\n\n"
        "Output ONLY valid JSON. "
        "No explanation. No markdown. No code "
        "blocks. Just the JSON object.\n\n"
        "Required format:\n"
        "{\n"
        "  \"goal\": \"brief description of "
        "what the user wants\",\n"
        "  \"steps\": [\n"
        "    {\n"
        "      \"tool\": \"tool_name\",\n"
        "      \"args\": {},\n"
        "      \"description\": "
        "\"what this step does\"\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- Only include steps that are directly "
        "needed to answer the request.\n"
        "- The last step must always be: "
        "{\"tool\": \"respond\", \"args\": {}}.\n"
        "- If no tools are needed, include only "
        "the respond step.\n"
        "- Keep plans minimal. "
        "Do not add unnecessary steps.\n"
        "- Output only the JSON. Nothing else."
    )

    def __init__(
        self,
        llm_client,
        tool_registry
    ):
        self.llm = llm_client
        self.tools = tool_registry

    def plan(
        self,
        text,
        memory,
        character_manager
    ):
        """
        Produce a Plan for the given user
        message by asking the LLM to reason
        about what steps are needed.

        Falls back to a minimal respond-only
        plan if the LLM is unavailable or
        returns unparseable output.
        """

        tool_list = self._format_tools()
        context_summary = self._format_context(
            memory
        )

        user_message = (
            f"User said: \"{text}\"\n\n"
            f"Available tools:\n{tool_list}\n\n"
            f"Current context:\n{context_summary}"
        )

        messages = [
            {
                "role": "user",
                "content": user_message
            }
        ]

        raw = self.llm.chat(
            self.SYSTEM,
            messages
        )

        plan = self._parse_plan(raw)

        if plan:

            print(
                f"[Planner] Goal: {plan.goal}"
            )

            for step in plan.steps:
                print(
                    f"  -> {step.tool}"
                    f"({json.dumps(step.args)})"
                )

        else:

            print(
                "[Planner] Could not parse plan. "
                "Using fallback."
            )

            plan = self._fallback_plan()

        return plan

    # --- Private helpers ---

    def _format_tools(self):

        tools = self.tools.list_tools()

        lines = []

        for t in tools:
            lines.append(
                f"- {t['name']}: "
                f"{t['description']}"
            )

        lines.append(
            "- respond: Generate the final "
            "conversational response "
            "(always the last step)"
        )

        return "\n".join(lines)

    def _format_context(self, memory):

        lines = []

        profile = memory.user_profile.data

        if profile:
            facts = ", ".join(
                f"{k}={v}"
                for k, v in profile.items()
            )
            lines.append(
                f"Known user facts: {facts}"
            )

        projects = memory.list_projects()

        if projects:
            lines.append(
                f"Active projects: "
                f"{', '.join(projects)}"
            )

        return (
            "\n".join(lines)
            if lines
            else "No special context."
        )

    def _parse_plan(self, raw):

        if not raw:
            return None

        try:

            # Strip markdown fences if present
            clean = re.sub(
                r'```[a-zA-Z]*\n?',
                '',
                raw
            ).strip()

            # Extract the first JSON object found
            match = re.search(
                r'\{.*\}',
                clean,
                re.DOTALL
            )

            if not match:
                return None

            data = json.loads(match.group())

            goal = data.get(
                "goal",
                "Respond to user"
            )

            steps_data = data.get("steps", [])

            steps = []

            for s in steps_data:

                tool = s.get("tool", "respond")
                args = s.get("args", {})
                desc = s.get("description", "")

                steps.append(
                    PlanStep(
                        tool=tool,
                        args=args,
                        description=desc
                    )
                )

            # Always ensure plan ends with respond
            if (
                not steps
                or steps[-1].tool != "respond"
            ):
                steps.append(
                    PlanStep(
                        tool="respond",
                        args={},
                        description=(
                            "Generate response"
                        )
                    )
                )

            return Plan(goal=goal, steps=steps)

        except Exception as e:

            print(f"[Planner] Parse error: {e}")

            return None

    def _fallback_plan(self):

        return Plan(
            goal="Respond to user message",
            steps=[
                PlanStep(
                    tool="respond",
                    args={},
                    description=(
                        "Generate conversational "
                        "response"
                    )
                )
            ]
        )