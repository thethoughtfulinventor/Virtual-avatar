import json
import re


class Planner:
    """
    Phase 6+7: Pre-response planning step.

    Decides character routing, response
    strategy, and which tools to run before
    the main LLM call.
    """

    SYSTEM = (
        "You are an internal routing and planning "
        "system for a digital companion application. "
        "Your only job is to analyze the user's "
        "message and produce a JSON plan.\n\n"
        "Reply ONLY with a valid JSON object. "
        "No markdown. No explanation. No extra text.\n\n"
        "JSON schema:\n"
        "{\n"
        '  "best_character": "CharacterName or null",\n'
        '  "reason": "one sentence",\n'
        '  "response_strategy": '
        '"direct|elaborate|question|brief",\n'
        '  "tools_needed": [\n'
        '    {"tool": "tool_name", '
        '"args": {}, "description": "one line"}\n'
        "  ]\n"
        "}\n\n"

        "CHARACTER ROUTING — read carefully:\n\n"
        "Set best_character to a name when:\n"
        "- The user directly asks to switch to or "
        "talk to a named character.\n"
        "- The task clearly requires the other "
        "character's specific expertise.\n\n"
        "Set best_character to null when:\n"
        "- The request is conditional/future-tense: "
        "contains 'when', 'if', 'once', 'after', "
        "'next time', 'later'.\n"
        "- Either character could handle it.\n"
        "- When in doubt, do not switch.\n\n"
        "Never set best_character to the current "
        "character's own name.\n\n"

        "RESPONSE STRATEGY:\n"
        "  brief     = trivial, greeting, yes/no.\n"
        "  direct    = clear factual answer.\n"
        "  elaborate = technical or complex topic.\n"
        "  question  = request is too vague.\n\n"

        "TOOLS:\n"
        "Only add tools to tools_needed when their "
        "output is genuinely required to answer the "
        "question. Leave as [] if current context "
        "is sufficient.\n"
        "- Use web_search when the question requires "
        "current or real-time information.\n"
        "- Use file_list / file_read when the user "
        "asks about files or folder contents.\n"
        "- Use terminal_run for system queries or "
        "when the user asks to run a command.\n"
        "- Use system_stats for CPU, RAM, or GPU "
        "questions.\n"
        "- Use app_launch only when the user "
        "explicitly asks to open an application.\n"
        "- Do NOT use tools for memory recall — "
        "that data is already in the system prompt.\n"
        "- Each entry: "
        '{"tool": "name", "args": {...}, '
        '"description": "one line"}.'
    )

    def __init__(
        self,
        llm_client,
        roster,
        tool_registry=None
    ):

        self.llm = llm_client
        self.roster = roster
        self.tool_registry = tool_registry

    def plan(
        self,
        text,
        current_character,
        recent_context=None
    ):

        current_name = current_character.get_name()

        roster_summary = self.roster.get_summary(
            exclude=current_name
        )

        context_snippet = self._format_context(
            recent_context
        )

        tool_block = self._format_tools()

        prompt = (
            f"Current active character: {current_name}\n\n"
            f"Other available characters:\n"
            f"{roster_summary}\n\n"
            f"Recent conversation:\n"
            f"{context_snippet}\n\n"
            f"{tool_block}"
            f"User message: {text}\n\n"
            "Produce a JSON plan."
        )

        messages = [
            {"role": "user", "content": prompt}
        ]

        raw = self.llm.chat(self.SYSTEM, messages)

        plan = self._parse(raw, current_name)

        # Log the plan concisely
        tools_log = (
            ", ".join(
                t.get("tool", "?")
                for t in plan["tools_needed"]
            )
            if plan["tools_needed"]
            else "none"
        )

        print(
            f"[Planner] strategy={plan['response_strategy']}"
            f", tools={tools_log}"
            + (
                f", route_to={plan['best_character']}"
                f" ({plan['reason']})"
                if plan["best_character"]
                else ""
            )
        )

        return plan

    def _format_tools(self):
        """
        Builds the available tools block for
        the planning prompt.
        """

        if not self.tool_registry:
            return ""

        tools = self.tool_registry.list_tools()

        if not tools:
            return ""

        lines = ["Available tools:"]

        for t in tools:
            lines.append(
                f"  {t['name']}: {t['description']}"
            )

        return "\n".join(lines) + "\n\n"

    def _format_context(self, recent_context):

        if not recent_context:
            return "(no recent context)"

        lines = []

        for entry in recent_context[-4:]:

            role = entry.get("role", "user")
            content = entry.get("content", "")

            snippet = (
                content[:120] + "..."
                if len(content) > 120
                else content
            )

            lines.append(f"{role}: {snippet}")

        return "\n".join(lines)

    def _parse(self, raw, current_name):

        default = {
            "best_character": None,
            "reason": "",
            "response_strategy": "direct",
            "tools_needed": []
        }

        if not raw:
            return default

        try:

            clean = re.sub(
                r"```[a-z]*", "", raw
            ).strip("` \n")

            data = json.loads(clean)

            best = data.get("best_character")

            if (
                best
                and best.lower() == current_name.lower()
            ):
                best = None

            if best:
                canonical = self.roster.resolve_name(best)
                best = canonical

            valid_strategies = {
                "direct", "elaborate",
                "question", "brief"
            }

            strategy = data.get(
                "response_strategy", "direct"
            )

            if strategy not in valid_strategies:
                strategy = "direct"

            # Validate tools_needed entries
            raw_tools = data.get("tools_needed", [])
            tools_needed = []

            for entry in raw_tools:

                if not isinstance(entry, dict):
                    continue

                tool_name = entry.get("tool", "")

                if not tool_name:
                    continue

                # Only include tools that are
                # actually registered
                if (
                    self.tool_registry
                    and not self.tool_registry.has(
                        tool_name
                    )
                ):
                    print(
                        f"[Planner] Unknown tool "
                        f"skipped: {tool_name}"
                    )
                    continue

                tools_needed.append(entry)

            return {
                "best_character": best,
                "reason": data.get("reason", ""),
                "response_strategy": strategy,
                "tools_needed": tools_needed
            }

        except Exception:
            return default