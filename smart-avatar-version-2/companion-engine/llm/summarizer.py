class Summarizer:

    SYSTEM = (
        "You are a memory summarizer for a digital "
        "companion. Summarize the conversation below "
        "in 1-3 concise sentences. Capture what was "
        "discussed, any facts the user or assistant shared, any "
        "progress or decisions made, and make sure to included the assistant's name so we can tell which ai was talking when and about what. Be specific — "
        "never write vague statements like "
        "'they had a conversation'."
    )

    def __init__(self, llm_client):
        self.llm = llm_client

    def summarize(self, entries):

        if not entries:
            return None

        lines = []

        for entry in entries:
            role = entry.get("role", "user")
            content = entry.get("content", "")
            speaker = "User" if role == "user" else "Assistant"
            lines.append(f"{speaker}: {content}")

        conversation = "\n".join(lines)

        messages = [
            {
                "role": "user",
                "content": (
                    f"Summarize this conversation:\n\n"
                    f"{conversation}"
                )
            }
        ]

        result = self.llm.chat(self.SYSTEM, messages)

        return result or None