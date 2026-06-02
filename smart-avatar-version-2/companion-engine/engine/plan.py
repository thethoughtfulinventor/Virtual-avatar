class PlanStep:
    """
    A single step in an execution plan.

    tool        — name of the tool to run
    args        — arguments passed to the tool
    description — human-readable label (also
                  used in context output)
    result      — filled in by PlanExecutor
    success     — True if the tool ran cleanly
    """

    def __init__(
        self,
        tool,
        args=None,
        description=""
    ):
        self.tool = tool
        self.args = args or {}
        self.description = description
        self.result = None
        self.success = False


class Plan:
    """
    A structured plan produced by the Planner.

    goal  — brief description of what the user
            wants to achieve
    steps — ordered list of PlanStep objects

    The final step is always tool="respond",
    which signals that execution is complete
    and the LLM should now generate its reply.
    """

    def __init__(
        self,
        goal,
        steps=None
    ):
        self.goal = goal
        self.steps = steps or []

    def get_action_steps(self):
        """
        Returns all steps except the terminal
        respond step. These are the steps that
        actually retrieve or modify data.
        """
        return [
            s for s in self.steps
            if s.tool != "respond"
        ]

    def has_results(self):

        return any(
            s.result
            for s in self.get_action_steps()
        )

    def format_results(self):
        """
        Formats executed step results into a
        plain-text context block for injection
        into the LLM system prompt.
        """
        lines = []

        for step in self.get_action_steps():

            if step.result:

                label = (
                    step.description
                    or step.tool
                )

                lines.append(
                    f"{label}: {step.result}"
                )

        return "\n".join(lines)