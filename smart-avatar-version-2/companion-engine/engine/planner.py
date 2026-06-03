import json
import re


class Planner:
    """
    Phase 6: Pre-response planning step.

    Runs before the main LLM call on every
    conversational turn. Decides:

    1. Which character is best suited to respond
       (character routing)
    2. What response strategy to use
       (direct, elaborate, question, brief)
    3. tools_needed placeholder for Phase 7+

    Only runs on 'conversation' intent to avoid
    adding latency to simple system commands.
    """

    SYSTEM = (
        "You are an internal routing and planning "
        "system for a digital companion application. "
        "Your only job is to analyze the user's "
        "message and decide which character should "
        "respond and what strategy fits best.\n\n"
        "Reply ONLY with a valid JSON object. "
        "No markdown. No explanation. No extra text.\n\n"
        "JSON schema:\n"
        "{\n"
        '  "best_character": "CharacterName or null",\n'
        '  "reason": "one sentence",\n'
        '  "response_strategy": '
        '"direct|elaborate|question|brief",\n'
        '  "tools_needed": []\n'
        "}\n\n"
        "ROUTING RULES — read carefully:\n\n"
        "Set best_character to a character name when:\n"
        "- The user directly and immediately asks to "
        "switch to or talk to a named character "
        "(e.g. 'can you switch to X', 'bring in X', "
        "'I want to talk to X', 'get X for me'). "
        "These are immediate requests — route to that "
        "character.\n"
        "- The user's actual task clearly requires the "
        "other character's specific expertise and the "
        "mismatch with the current character is "
        "obvious.\n\n"
        "Set best_character to null (do NOT switch) when:\n"
        "- The request is CONDITIONAL or FUTURE-TENSE: "
        "it contains trigger words like 'when', 'if', "
        "'once', 'after', 'next time', 'later' "
        "(e.g. 'when I say apple switch to X', "
        "'if I ask about code switch to Y'). "
        "The condition has not been met — do not switch.\n"
        "- The user is asking what a character would say "
        "without wanting to actually switch.\n"
        "- Either character could handle the request "
        "reasonably well.\n"
        "- When in doubt, do not switch.\n\n"
        "Never set best_character to the current "
        "character's own name.\n\n"
        "response_strategy — pick the BEST fit:\n"
        "    brief     = trivial/simple question, "
        "greeting, or yes/no — ONE sentence max. "
        "Use this for anything a child could answer.\n"
        "    direct    = clear factual answer, "
        "moderate complexity — a short paragraph.\n"
        "    elaborate = in-depth explanation, "
        "technical or complex topic — go into detail.\n"
        "    question  = request is too vague to answer "
        "— ask for clarification first.\n\n"
        "tools_needed: always []."
    )

    def __init__(self, llm_client, roster):

        self.llm = llm_client
        self.roster = roster

    def plan(
        self,
        text,
        current_character,
        recent_context=None
    ):
        """
        Analyzes a user message and returns
        a routing + strategy plan.

        Returns:
        {
            "best_character": str | None,
            "reason": str,
            "response_strategy": str,
            "tools_needed": list
        }
        """

        current_name = current_character.get_name()

        roster_summary = self.roster.get_summary(
            exclude=current_name
        )

        context_snippet = self._format_context(
            recent_context
        )

        prompt = (
            f"Current active character: {current_name}\n\n"
            f"Other available characters:\n"
            f"{roster_summary}\n\n"
            f"Recent conversation:\n"
            f"{context_snippet}\n\n"
            f"User message: {text}\n\n"
            "Should the current character handle this, "
            "or is another character a clearly better fit?"
        )

        messages = [
            {"role": "user", "content": prompt}
        ]

        raw = self.llm.chat(self.SYSTEM, messages)

        plan = self._parse(raw, current_name)

        print(
            f"[Planner] strategy={plan['response_strategy']}"
            + (
                f", route_to={plan['best_character']}"
                f" ({plan['reason']})"
                if plan["best_character"]
                else ""
            )
        )

        return plan

    def _format_context(self, recent_context):

        if not recent_context:
            return "(no recent context)"

        lines = []

        for entry in recent_context[-4:]:

            role = entry.get("role", "user")
            content = entry.get("content", "")

            # Truncate long entries for the planner
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

            # Strip markdown fences if the LLM
            # ignores the no-markdown instruction
            clean = re.sub(
                r"```[a-z]*", "", raw
            ).strip("` \n")

            data = json.loads(clean)

            best = data.get("best_character")

            # Reject a switch back to self
            if (
                best
                and best.lower() == current_name.lower()
            ):
                best = None

            # Validate against known characters
            if best:
                canonical = self.roster.resolve_name(best)
                best = canonical  # None if not found

            valid_strategies = {
                "direct",
                "elaborate",
                "question",
                "brief"
            }

            strategy = data.get(
                "response_strategy", "direct"
            )

            if strategy not in valid_strategies:
                strategy = "direct"

            return {
                "best_character": best,
                "reason": data.get("reason", ""),
                "response_strategy": strategy,
                "tools_needed": data.get(
                    "tools_needed", []
                )
            }

        except Exception:
            return default