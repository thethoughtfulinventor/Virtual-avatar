class BaseTool:
    """
    Base class for all planning tools.

    Subclasses must define:

        name        — the string identifier
                      used in plans
                      (e.g. "memory_recall")

        description — shown to the planner LLM
                      so it knows when to use
                      this tool

        run(args, context) — executes the tool
                             and returns a str

    The context dict currently contains:
        "memory" — the MemoryManager instance

    Additional keys will be added in later
    phases (e.g. "system" for the observation
    system, "browser" for web skills).
    """

    name = "base"
    description = "Base tool. Do not use directly."

    def run(self, args, context):

        raise NotImplementedError(
            f"Tool '{self.name}' "
            f"must implement run()."
        )