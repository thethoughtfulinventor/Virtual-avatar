class Summarizer:

    SYSTEM = (
        "Summarize the conversation in 1–3 concise sentences, "
        "capturing key facts, decisions, and progress. "
        "Explicitly identify every persona change by stating "
        "'The persona switches to [Character Name]' or "
        "'[Character Name] takes over' at the exact point the character changes."
        " Ensure the assistant's name is included to attribute statements correctly, "
        "avoiding vague descriptions of the dialogue flow."
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