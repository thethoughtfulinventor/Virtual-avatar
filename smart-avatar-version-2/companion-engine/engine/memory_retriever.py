class MemoryRetriever:

    def __init__(
        self,
        memory_manager
    ):

        self.memory = (
            memory_manager
        )

    def retrieve(
        self,
        text
    ):

        memories = []

        words = text.lower().split()

        for word in words:

            value = (
                self.memory.recall(word)
            )

            if value:

                memories.append(
                    {
                        "key": word,
                        "value": value
                    }
                )

        return memories