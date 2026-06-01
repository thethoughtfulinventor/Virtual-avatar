class ResponseGenerator:

    def generate(
        self,
        intent,
        text,
        memories,
        character
    ):

        name = character.get(
            "name",
            "Assistant"
        )

        personality = character.get(
            "personality",
            ""
        )

        traits = (
            character["personality"]
            ["traits"]
        )

        style = (
            character["personality"]
            ["speaking_style"]
        )

        if intent == "greeting":

            return (
                f"Hello. I'm {name}. "
                f"How can I help?"
            )

        if intent == "memory_store":

            return (
                f"I'll remember that."
            )

        if intent == "memory_recall":

            return (
                f"Checking my memory."
            )

        if memories:

            memory_text = ", ".join(
                [
                    f"{m['key']}={m['value']}"
                    for m in memories
                ]
            )

            return (
                f"As a {personality.lower()} assistant, "
                f"I remember: {memory_text}"
            )

        return (
            f"I am {character['name']}. "
            f"My traits are: "
            f"{', '.join(traits)}."
        )