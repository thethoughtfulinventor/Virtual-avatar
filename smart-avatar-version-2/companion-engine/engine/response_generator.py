class ResponseGenerator:

    def generate(
        self,
        intent,
        text,
        memories,
        character,
        modifier=None
    ):

        if modifier is None:
            modifier = {}

        name = character.get_name()

        traits = character.get_traits()

        # Modifier speaking_style overrides
        # character default when present
        style = (
            modifier.get("speaking_style")
            or character.get_style()
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
                f"As a {style} assistant, "
                f"I remember: {memory_text}"
            )

        return (
            f"I am {name}. "
            f"My traits are: "
            f"{', '.join(traits)}."
        )