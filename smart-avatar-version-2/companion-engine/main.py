import os

from engine.state_manager import StateManager
from engine.event_bus import EventBus
from engine.service_manager import ServiceManager
from engine.plugin_manager import PluginManager
from engine.character_loader import CharacterLoader
from engine.tool_registry import ToolRegistry
from engine.brain import Brain

from memory.memory_manager import MemoryManager

from tools.memory_tools import (
    MemoryRecallTool,
    MemoryListTool
)
from tools.project_tools import (
    ProjectLookupTool,
    ProjectsListTool
)

service_manager = None
brain_instance = None


def select_character():

    characters_dir = "characters"

    available = []

    for entry in os.listdir(
        characters_dir
    ):

        char_path = os.path.join(
            characters_dir,
            entry
        )

        config_path = os.path.join(
            char_path,
            "character.json"
        )

        if (
            os.path.isdir(char_path)
            and os.path.exists(config_path)
        ):

            available.append(entry)

    available.sort()

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

    for i, name in enumerate(
        available, 1
    ):

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


def on_engine_started(data):
    print("Startup event received")


def on_user_input(text):

    memory = service_manager.get("memory")

    result = brain_instance.process(text)

    intent = result["intent"]

    print(f"[INTENT] {intent}")

    print(
        f"{brain_instance.character_manager.get_name()}"
        f": {result['response']}"
    )

    # --- System command routing ---
    # Brain has already generated a response and
    # stored context. These blocks handle the
    # actual memory operations the commands imply.

    if intent == "memory_store":

        try:

            key_value = text.replace(
                "remember ", ""
            )

            key, value = key_value.split("=", 1)

            memory.remember(
                key.strip(),
                value.strip()
            )

            print(f"Stored: {key.strip()}")

        except ValueError:

            print("Usage: remember key=value")

        return

    if intent == "memory_recall":

        key = text.replace(
            "recall ", ""
        ).strip()

        value = memory.recall(key)

        print(f"Memory: {value}")

        return

    if intent == "project_create":

        project_name = text.replace(
            "create project ", ""
        ).strip()

        memory.create_project(project_name)

        print(f"Created project: {project_name}")

        return

    if intent == "project_lookup":

        project_name = text.replace(
            "project ", ""
        ).strip()

        project = memory.get_project(project_name)

        if project:
            print(project)
        else:
            print("Project not found")

        return

    if intent == "projects_list":

        projects = memory.list_projects()

        if projects:
            print(projects)
        else:
            print("No projects found")

        return

    if intent == "episode_create":

        summary = text.replace(
            "episode ", ""
        ).strip()

        memory.add_episode(summary)

        print("Episode stored.")

        return

    if intent == "episode_list":

        episodes = memory.get_recent_episodes()

        for episode in episodes:
            print(
                f"{episode['timestamp']} "
                f"- {episode['summary']}"
            )

        return

    if intent == "context_view":

        entries = memory.get_recent_context()

        for entry in entries:
            print(
                f"[{entry['role']}] "
                f"{entry['content']}"
            )

        return

    if intent == "context_clear":

        memory.recent_context.clear()

        print("Context cleared.")

        return

    if intent == "life_event_create":

        description = text.replace(
            "life event ", ""
        ).strip()

        memory.add_life_event(description)

        print("Life event stored.")

        return

    if intent == "life_events_list":

        events = memory.get_life_events()

        for event in events:
            print(
                f"{event['timestamp']} "
                f"- {event['description']}"
            )

        return

    if intent == "state_view":

        state = (
            brain_instance
            .emotional_manager
            .get_all()
        )

        dominant = (
            brain_instance
            .emotional_manager
            .get_dominant()
        )

        print(f"Dominant state: {dominant}")

        for key, value in state.items():
            print(f"  {key}: {value:.2f}")

        return

    # Default: conversation
    # Context is stored inside brain.process().
    print(f"[EVENT] user_input: {text}")


def main():

    print("=" * 40)
    print("Character CORE ENGINE")
    print("=" * 40)

    state_manager = StateManager()

    event_bus = EventBus()

    global service_manager

    service_manager = ServiceManager()

    plugin_manager = PluginManager()

    memory_manager = MemoryManager()

    service_manager.register(
        "memory",
        memory_manager
    )

    # Phase 6: Register planning tools
    tool_registry = ToolRegistry()
    tool_registry.register(MemoryRecallTool())
    tool_registry.register(MemoryListTool())
    tool_registry.register(ProjectLookupTool())
    tool_registry.register(ProjectsListTool())

    service_manager.register(
        "tool_registry",
        tool_registry
    )

    context_count = len(
        memory_manager.get_recent_context(100)
    )

    print(
        f"Restored "
        f"{context_count} "
        f"context entries."
    )

    event_bus.subscribe(
        "engine_started",
        on_engine_started
    )

    event_bus.subscribe(
        "user_input",
        on_user_input
    )

    character_loader = CharacterLoader()

    selected = select_character()

    character = character_loader.load(
        f"characters/{selected}"
    )

    state_manager.set(
        "active_character",
        character
    )

    print(f"Loaded Character: {character['name']}")

    brain = Brain(
        state_manager,
        event_bus,
        service_manager
    )

    global brain_instance

    brain_instance = brain

    print("Core systems initialized")

    event_bus.emit("engine_started")

    print("Engine running")

    while True:

        command = input("> ")

        print()

        if command.lower() in ["quit", "exit"]:
            break

        event_bus.emit("user_input", command)

        print()


if __name__ == "__main__":
    main()