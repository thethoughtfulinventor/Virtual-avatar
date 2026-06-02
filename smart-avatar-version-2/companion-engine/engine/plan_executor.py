class PlanExecutor:
    """
    Phase 6: Execution layer.

    The PlanExecutor runs each non-respond step
    in a Plan using the ToolRegistry, collects
    results from each tool, and returns them as
    a formatted string.

    This string is then injected into the LLM
    system prompt as "RETRIEVED CONTEXT" so the
    model has real data when generating its reply.

    The "respond" step is not executed here —
    it is a terminal marker indicating the plan
    is complete and control should pass back to
    the Brain's main LLM call.
    """

    def __init__(self, tool_registry):
        self.tools = tool_registry

    def execute(self, plan, memory):
        """
        Run all action steps in the plan.

        Returns a formatted context string
        for injection into the system prompt.
        Returns an empty string if no action
        steps were present or all failed.
        """

        context = {"memory": memory}

        for step in plan.steps:

            if step.tool == "respond":
                continue

            tool = self.tools.get(step.tool)

            if not tool:

                print(
                    f"[Executor] Unknown tool: "
                    f"{step.tool}"
                )

                step.result = (
                    f"Tool '{step.tool}' "
                    f"not available."
                )

                step.success = False

                continue

            try:

                result = tool.run(
                    step.args,
                    context
                )

                step.result = result
                step.success = True

                preview = (
                    result[:60] + "..."
                    if len(result) > 60
                    else result
                )

                print(
                    f"[Executor] {step.tool}: "
                    f"{preview}"
                )

            except Exception as e:

                step.result = f"Error: {e}"
                step.success = False

                print(
                    f"[Executor] Error in "
                    f"{step.tool}: {e}"
                )

        return plan.format_results()