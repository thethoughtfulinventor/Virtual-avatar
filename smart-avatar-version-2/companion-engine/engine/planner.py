import json
import re

class Planner:

    def __init__(
        self,
        llm_client,
        roster,
        tool_registry=None
    ):
        self.llm = llm_client
        self.roster = roster
        self.tool_registry = tool_registry

    SYSTEM = """
    You are an internal planning system.

    Respond ONLY with valid JSON.

    Schema:

    {
    "best_character": "CharacterName or null",
    "reason": "one sentence",
    "response_strategy": "direct|elaborate|question|brief",
    "tools_needed": [
        {
        "tool": "tool_name",
        "args": {},
        "description": "one line"
        }
    ]
    }

    Rules:
    - Always include args.
    - Never omit args.
    - Use {} when no arguments exist.
    - Use exact tool argument names shown below.
    """

    def plan(
        self,
        text,
        current_character,
        recent_context=None
    ):

        text = text.strip()

        fast_plan = self._fast_path(
            text,
            current_character
        )

        if fast_plan:
            self._log_plan(fast_plan)
            return fast_plan

        prompt = self._build_prompt(
            text,
            current_character,
            recent_context
        )

        raw = self.llm.chat(
            self.SYSTEM,
            [{"role": "user", "content": prompt}]
        )

        plan = self._parse(
            raw,
            current_character.get_name()
        )

        self._log_plan(plan)

        return plan

    def _fast_path(
    self,
    text,
    current_character
    ):

        lower = text.lower()

        launch = re.match(
            r"^(open|launch|start|run)\s+(.+)$",
            text,
            re.IGNORECASE
        )

        if launch:

            app = launch.group(2).strip()

            return {
                "best_character": None,
                "reason": "",
                "response_strategy":
                    "direct",
                "tools_needed": [
                    {
                        "tool": "app_launch",
                        "args": {
                            "app": app
                        },
                        "description":
                            f"Launch {app}"
                    }
                ]
            }

        if (
            "cpu" in lower
            or "ram" in lower
            or "memory usage" in lower
            or "gpu" in lower
        ):

            return {
                "best_character": None,
                "reason": "",
                "response_strategy":
                    "direct",
                "tools_needed": [
                    {
                        "tool":
                            "system_stats",
                        "args": {},
                        "description":
                            "Retrieve system stats"
                    }
                ]
            }

        return None

    def _build_prompt(
    self,
    text,
    current_character,
    recent_context
    ):

        current_name = (
            current_character.get_name()
        )

        roster_summary = (
            self.roster.get_summary(
                exclude=current_name
            )
        )

        context = (
            self._format_context(
                recent_context
            )
        )

        tools = self._tool_schema()

        return (
            f"Current character:\n"
            f"{current_name}\n\n"

            f"Other characters:\n"
            f"{roster_summary}\n\n"

            f"Recent context:\n"
            f"{context}\n\n"

            f"{tools}\n\n"

            f"User message:\n"
            f"{text}\n\n"

            "Generate plan."
        )

    def _tool_schema(self):

        if not self.tool_registry:
            return ""

        tools = self.tool_registry.list_tools()

        lines = [
            "AVAILABLE TOOLS"
        ]

        for t in tools:

            name = t["name"]

            lines.append(
                f"\n{name}"
            )

            lines.append(
                f"Description: "
                f"{t['description']}"
            )

            if name == "app_launch":

                lines.append(
                    "Args:"
                )

                lines.append(
                    "  app (string)"
                )

            elif name == "terminal_run":

                lines.append(
                    "Args:"
                )

                lines.append(
                    "  command (string)"
                )

            elif name == "web_search":

                lines.append(
                    "Args:"
                )

                lines.append(
                    "  query (string)"
                )

            else:

                lines.append(
                    "Args: {}"
                )

        return "\n".join(lines)

    def _format_context(
    self,
    recent_context
    ):

        if not recent_context:
            return "(none)"

        lines = []

        for entry in recent_context[-4:]:

            role = entry.get(
                "role",
                "user"
            )

            content = entry.get(
                "content",
                ""
            )

            if len(content) > 120:
                content = (
                    content[:120]
                    + "..."
                )

            lines.append(
                f"{role}: {content}"
            )

        return "\n".join(lines)

    def _parse(
    self,
    raw,
    current_name
    ):

        default = {
            "best_character": None,
            "reason": "",
            "response_strategy":
                "direct",
            "tools_needed": []
        }

        try:

            clean = (
                raw
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

            print("\n=== RAW PLAN ===")
            print(raw)
            print("================\n")

            data = json.loads(clean)

            if (
                data.get(
                    "best_character"
                )
                == current_name
            ):
                data[
                    "best_character"
                ] = None

            valid = []

            for tool in data.get(
                "tools_needed",
                []
            ):

                if (
                    not isinstance(
                        tool,
                        dict
                    )
                ):
                    continue

                tool.setdefault(
                    "args",
                    {}
                )

                valid.append(tool)

            data[
                "tools_needed"
            ] = valid

            return data

        except Exception as e:

            print(
                "[Planner] Parse error:",
                e
            )

            return default

    def _log_plan(
    self,
    plan
    ):

        tools = (
            ", ".join(
                t["tool"]
                for t in plan[
                    "tools_needed"
                ]
            )
            if plan[
                "tools_needed"
            ]
            else "none"
        )

        print(
            f"[Planner] "
            f"strategy="
            f"{plan['response_strategy']}, "
            f"tools={tools}"
        )
