from characters.character_manager import CharacterManager
from emotion.emotional_manager import EmotionalManager
from llm.model_config import ModelConfig
from conversation.response_processor import ResponseProcessor

class CharacterRouter:

    def __init__(self, roster, state_manager, prompt_builder, llm_client, tool_registry=None):
        self.roster = roster
        self.state_manager = state_manager
        self.prompt_builder = prompt_builder
        self.llm_client = llm_client
        self.tool_registry = tool_registry # Ensure this is passed from Brain
        
        self.response_processor = ResponseProcessor(self.tool_registry)
        
        self.character = None
        self.character_manager = None
        self.emotional_manager = None

    # --------------------------------------------------
    # Character switching
    # --------------------------------------------------

    def switch_character(self, name: str):
        print(f"[Router] Attempting switch to: '{name}'")
        canonical = self.roster.resolve_name(name)
        print(f"[Router] Resolved canonical name: {canonical}")
        
        if not canonical:
            return None

        character_data = self.roster.get(canonical)
        print(f"[Router] Character data retrieved: {character_data is not None}")
        
        if not character_data:
            return None

        self.state_manager.set("active_character", character_data)
        self.character = character_data
        self.character_manager = CharacterManager(character_data)
        
        char_name = self.character_manager.get_name()
        print(f"[Router] Character Manager Name: {char_name}")
        
        self.emotional_manager = EmotionalManager(char_name)
        
        print(f"[Brain] Character switched to {canonical}")
        return canonical   
    
    def _handle_switch(self, text: str, memory) -> dict:
        t_lower = text.lower().strip()
        name = (
            t_lower
            .replace("switch character ", "")
            .replace("switch to ", "")
            .strip()
        )

        canonical = self.switch_character(name)

        if not canonical:
            available = ", ".join(self.roster.get_names())
            response = (
                f"No character named '{name}' found. "
                f"Available: {available}"
            )
            return {
                "intent":            "switch_character",
                "response":          response,
                "memories":          [],
                "emotional_state":   self.emotional_manager.get_dominant(),
                "character_switched": False,
                "new_character":     None,
            }

        system_prompt = self.prompt_builder.build_system_prompt(
            self.character_manager,
            self.emotional_manager,
            memory,
            roster=self.roster,
        )

        recent = memory.get_recent_context(ModelConfig.MAX_CONTEXT)
        messages = self.prompt_builder.format_context(recent, canonical)

        messages.append({
            "role": "user",
            "content": (
                f"{text}\n"
                f"[You ({canonical}) just took over. "
                f"Respond ONLY to this current message. "
                f"Do not revisit earlier questions from "
                f"the conversation history.]"
            ),
        })

        response = self.llm_client.chat(system_prompt, messages)

        if response:
            response = self.response_processor.process(response, memory)

        if not response:
            response = f"{canonical} online."

        memory.add_context("user", text)
        memory.add_context("assistant", response, canonical)

        return {
            "intent":            "switch_character",
            "response":          response,
            "memories":          [],
            "emotional_state":   self.emotional_manager.get_dominant(),
            "character_switched": True,
            "new_character":     canonical,
        }