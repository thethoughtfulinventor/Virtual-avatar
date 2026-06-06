import os

from core.state_manager import StateManager
from core.event_bus import EventBus
from core.service_manager import ServiceManager
from core.plugin_manager import PluginManager
from characters.character_loader import CharacterLoader
from characters.character_roster import CharacterRoster
from conversation.brain import Brain
from core.cuda_manager import CudaManager       # Phase 8 prep

from memory.memory_manager import MemoryManager

service_manager = None
brain_instance = None


def select_character(available):

    if not available:

        print(
            "No characters found "
            "in characters/ directory."
        )

        raise SystemExit(1)

    if len(available) == 1:

        print(
            f"Loading character: "
            f"{available[0]}"
        )

        return available[0]

    print("\nAvailable characters:")

    for i, name in enumerate(available, 1):
        print(f"  {i}. {name}")

    while True:

        choice = input(
            "\nSelect a character: "
        ).strip()

        if choice.isdigit():

            index = int(choice) - 1

            if 0 <= index < len(available):
                return available[index]

        if choice in available:
            return choice

        print(
            "Invalid selection. "
            "Please enter a number "
            "or character name."
        )


def on_engine_started(**kwargs):
    print("Startup event received")


def on_user_input(**kwargs):
    text = kwargs.get("text")
    if not text or not isinstance(text, str):
        return

    # ----------------------------
    # Safety guards (important)
    # ----------------------------
    global service_manager, brain_instance

    if service_manager is None or brain_instance is None:
        print("[WARN] service_manager or brain_instance not ready")
        return

    memory = service_manager.get("memory")
    if memory is None:
        print("[WARN] memory service not available")
        return

    try:
        result = brain_instance.process(text)
    except Exception as e:
        print(f"[Brain Error] {e}")
        return

    if not isinstance(result, dict):
        print("[Brain Error] Invalid response format")
        return

    intent = result.get("intent", "unknown")
    response = result.get("response", "")
    switched = result.get("character_switched", False)
    new_character = result.get("new_character")

    current_name = "unknown"
    if brain_instance.character_manager:
        current_name = brain_instance.character_manager.get_name()

    print(f"[INTENT] {intent}")

    if switched:
        print(f"[System] Switched to: {new_character}")

    # Only print real LLM output
    if response:
        print(f"{current_name}: {response}")

    # ----------------------------
    # SYSTEM INTENT HANDLING
    # ----------------------------

    if intent == "switch_character":
        return

    if intent == "memory_store":
        try:
            key_value = text.replace("remember ", "")
            key, value = key_value.split("=", 1)
            memory.remember(key.strip(), value.strip())
            print(f"Stored: {key.strip()}")
        except Exception:
            print("Usage: remember key=value")
        return

    if intent == "memory_recall":
        key = text.replace("recall ", "").strip()
        print(f"Memory: {memory.recall(key)}")
        return

    if intent == "project_create":
        name = text.replace("create project ", "").strip()
        memory.create_project(name)
        print(f"Created project: {name}")
        return

    if intent == "project_lookup":
        name = text.replace("project ", "").strip()
        project = memory.get_project(name)
        print(project if project else "Project not found")
        return

    if intent == "projects_list":
        projects = memory.list_projects()
        print(projects if projects else "No projects found")
        return

    if intent == "episode_create":
        summary = text.replace("episode ", "").strip()
        memory.add_episode(summary)
        print("Episode stored.")
        return

    if intent == "episode_list":
        for ep in memory.get_recent_episodes():
            print(f"{ep['timestamp']} - {ep['summary']}")
        return

    if intent == "context_view":
        for entry in memory.get_recent_context():
            print(f"[{entry['role']}] {entry['content']}")
        return

    if intent == "context_clear":
        memory.recent_context.clear()
        print("Context cleared.")
        return

    if intent == "episode_clear":
        memory.episodic_memory.clear()
        print("Episodic memory cleared.")
        return

    if intent == "life_event_create":
        desc = text.replace("life event ", "").strip()
        memory.add_life_event(desc)
        print("Life event stored.")
        return

    if intent == "life_events_list":
        for event in memory.get_life_events():
            print(f"{event['timestamp']} - {event['description']}")
        return

    if intent == "state_view":
        state = brain_instance.emotional_manager.get_all()
        dominant = brain_instance.emotional_manager.get_dominant()

        print(f"Dominant state: {dominant}")
        for k, v in state.items():
            print(f"  {k}: {v:.2f}")
        return

    # ----------------------------
    # fallback debug output
    # ----------------------------
    print(f"[EVENT] user_input: {text}")


def main():

    print("=" * 40)
    print("Character CORE ENGINE")
    print("=" * 40)

    # --------------------------------------------------
    # CUDA detection — must run before Brain/OllamaClient
    # so that CUDA_VISIBLE_DEVICES is set before the
    # first HTTP connection to Ollama is made.
    # --------------------------------------------------
    cuda_manager = CudaManager()
    cuda_manager.print_status()
    print("-" * 40)

    state_manager = StateManager()   # no event_bus yet
    event_bus = EventBus()

    # NOW inject event bus into state manager if you want it
    state_manager.event_bus = event_bus

    global service_manager
    service_manager = ServiceManager()

    plugin_manager = PluginManager()
    memory_manager = MemoryManager()

    service_manager.register(
        "memory",
        memory_manager
    )

    # Register cuda_manager so subsystems (system_skill,
    # future avatar/initiative) can access GPU state without
    # spawning additional subprocesses.
    service_manager.register(
        "cuda",
        cuda_manager
    )

    context_count = len(
        memory_manager.get_recent_context(100)
    )

    print(
        f"Restored "
        f"{context_count} "
        f"context entries."
    )

    roster = CharacterRoster("characters")
    available = roster.get_names()

    print(
        f"Characters available: "
        f"{', '.join(available)}"
    )

    event_bus.subscribe("engine_started", on_engine_started)
    event_bus.subscribe("user_input", on_user_input)

    selected = select_character(available)

    character_loader = CharacterLoader()

    character = character_loader.load(
        f"characters/{selected}"
    )

    state_manager.set("active_character", character)

    print(f"Loaded Character: {character['name']}")

    brain = Brain(
        state_manager,
        event_bus,
        service_manager,
        roster
    )

    global brain_instance
    brain_instance = brain

    from skills.registry import register_skills
    register_skills(brain.tool_registry)

    print("Core systems initialized")

    event_bus.emit(
        "engine_started",
        timestamp="startup"
    )

    print("=" * 40)
    print("Commands:")
    print("  switch to <name>       — change character")
    print("  switch character <name>")
    print("  remember key=value     — store a fact")
    print("  recall <key>           — retrieve a fact")
    print("  state                  — emotional state")
    print("  projects               — list projects")
    print("  life events            — list life events")
    print("  episodes               — episodic memory")
    print("  context                — recent context")
    print("  clear context          — wipe context")
    print("  quit / exit            — shut down")
    print("=" * 40)

    print("Engine running")

    while True:

        try:
            command = input("> ")
        except (KeyboardInterrupt, EOFError):
            break

        print()

        if command.lower() in ["quit", "exit"]:
            break

        if not command.strip():
            continue

        event_bus.emit(
            "user_input",
            text=command
        )
        print()

    print("\nShutting down... Goodbye!")


if __name__ == "__main__":
    main()