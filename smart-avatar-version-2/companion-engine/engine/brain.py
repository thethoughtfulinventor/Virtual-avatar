from engine.intent_detector import (
    IntentDetector
)

from engine.response_generator import (
    ResponseGenerator
)

from engine.memory_retriever import (
    MemoryRetriever
)

from engine.character_manager import (
    CharacterManager
)


class Brain:

    def __init__(
        self,
        state_manager,
        event_bus,
        service_manager
    ):

        self.state_manager = (
            state_manager
        )

        self.event_bus = (
            event_bus
        )

        self.service_manager = (
            service_manager
        )

        self.intent_detector = (
            IntentDetector()
        )

        self.response_generator = (
            ResponseGenerator()
        )

        memory = service_manager.get(
            "memory"
        )

        self.memory_retriever = (
            MemoryRetriever(memory)
        )

        self.character = (
            state_manager.get(
                "active_character"
            )
        )

        self.character_manager = (
            CharacterManager(
                self.character
            )
        )

        print(
            "Brain initialized"
        )

    
    def process(
        self,
        text
    ):

        intent = (
            self.intent_detector
            .detect(text)
        )

        memories = (
            self.memory_retriever
            .retrieve(text)
        )

        response = (
            self.response_generator
            .generate(
                intent,
                text,
                memories,
                self.character_manager
            )
        )

        return {
            "intent": intent,
            "response": response,
            "memories": memories
        }