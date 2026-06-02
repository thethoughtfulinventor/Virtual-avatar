from tools.base_tool import BaseTool


class MemoryRecallTool(BaseTool):
    """
    Recalls a specific stored fact by key.

    Use when the user asks about something
    that may have been remembered, such as
    their name, preferences, or other
    facts they've shared before.
    """

    name = "memory_recall"
    description = (
        "Recalls a specific fact about the user "
        "by key name. Use when the user asks "
        "about something you may have stored "
        "about them (e.g. their name, favorite "
        "color, preferences)."
    )

    def run(self, args, context):

        memory = context.get("memory")

        if not memory:
            return "Memory system unavailable."

        key = args.get("key", "").strip()

        if not key:
            return "No key provided."

        value = memory.recall(key)

        if value is not None:
            return f"{key} = {value}"

        return f"No stored value for: {key}"


class MemoryListTool(BaseTool):
    """
    Lists all stored facts about the user.

    Use when the user asks what you remember
    about them, or when a broad profile view
    is needed to answer the question.
    """

    name = "memory_list"
    description = (
        "Lists all known facts about the user. "
        "Use when asked what you know or "
        "remember about the user in general."
    )

    def run(self, args, context):

        memory = context.get("memory")

        if not memory:
            return "Memory system unavailable."

        profile = memory.user_profile.data

        if not profile:
            return "No facts stored about the user yet."

        lines = [
            f"{k}: {v}"
            for k, v in profile.items()
        ]

        return "\n".join(lines)