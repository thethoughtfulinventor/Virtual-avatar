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
 
from engine.emotional_manager import (
    EmotionalManager
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
 
        self.emotional_manager = (
            EmotionalManager(
                self.character_manager
                .get_name()
            )
        )
 
        print(
            "Brain initialized"
        )
 
    def process(
        self,
        text
    ):
 
        # Step 1: detect intent
        intent = (
            self.intent_detector
            .detect(text)
        )
 
        # Step 2: retrieve relevant memories
        memories = (
            self.memory_retriever
            .retrieve(text)
        )
 
        # Step 3: update emotional state
        # based on text and intent
        self.emotional_manager.process(
            text,
            intent,
            self.character_manager
        )
 
        # Step 4: get dominant state
        # and its matching modifier
        dominant = (
            self.emotional_manager
            .get_dominant()
        )
 
        modifier = (
            self.character_manager
            .get_emotional_modifiers()
            .get(dominant, {})
        )
 
        # Step 5: generate response
        response = (
            self.response_generator
            .generate(
                intent,
                text,
                memories,
                self.character_manager,
                modifier
            )
        )
 
        return {
            "intent": intent,
            "response": response,
            "memories": memories,
            "emotional_state": dominant
        }