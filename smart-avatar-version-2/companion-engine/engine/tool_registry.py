class ToolRegistry:
    """
    Registry for planning tools.

    Tools registered here are made available
    to the Planner (which describes them to
    the LLM) and the PlanExecutor (which
    calls them during execution).

    Phase 7 skills will register themselves
    here once loaded, making them available
    to the planning system automatically.
    """

    def __init__(self):
        self.tools = {}

    def register(self, tool):

        self.tools[tool.name] = tool

        print(
            f"[ToolRegistry] Registered: "
            f"{tool.name}"
        )

    def get(self, name):
        return self.tools.get(name)

    def has(self, name):
        return name in self.tools

    def remove(self, name):

        if name in self.tools:
            del self.tools[name]

    def list_tools(self):
        """
        Returns a list of dicts with name and
        description — fed directly into the
        Planner's LLM prompt.
        """
        return [
            {
                "name": t.name,
                "description": t.description
            }
            for t in self.tools.values()
        ]

    def list_names(self):
        return list(self.tools.keys())