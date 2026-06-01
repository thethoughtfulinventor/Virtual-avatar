from engine.state_manager import StateManager
from engine.event_bus import EventBus
from engine.service_manager import ServiceManager
from engine.plugin_manager import PluginManager
from engine.character_loader import CharacterLoader
from engine.brain import Brain

from memory.memory_manager import MemoryManager
service_manager = None
brain_instance = None

def on_engine_started(data):
    print("Startup event received")


def on_user_input(text):

    memory = service_manager.get(
        "memory"
    )

    result = (
        brain_instance.process(
            text
        )
    )

    print(
        f"[INTENT] "
        f"{result['intent']}"
    )

    print(
        f"AIYA: "
        f"{result['response']}"
    )

    # User profile memory

    if text.startswith("remember "):

        try:

            key_value = text.replace(
                "remember ",
                ""
            )

            key, value = key_value.split(
                "=",
                1
            )

            memory.remember(
                key.strip(),
                value.strip()
            )

            print(
                f"Stored: {key.strip()}"
            )

        except ValueError:

            print(
                "Usage: remember key=value"
            )

        return

    if text.startswith("recall "):

        key = text.replace(
            "recall ",
            ""
        ).strip()

        value = memory.recall(
            key
        )

        print(
            f"Memory: {value}"
        )

        return

    # Project memory

    if text.startswith(
        "create project "
    ):

        project_name = text.replace(
            "create project ",
            ""
        ).strip()

        memory.create_project(
            project_name
        )

        print(
            f"Created project: {project_name}"
        )

        return

    if text.startswith(
        "project "
    ):

        project_name = text.replace(
            "project ",
            ""
        ).strip()

        project = memory.get_project(
            project_name
        )

        if project:

            print(project)

        else:

            print(
                "Project not found"
            )

        return

    if text == "projects":

        projects = memory.list_projects()

        if projects:

            print(projects)

        else:

            print(
                "No projects found"
            )

        return
    
    if text.startswith(
        "episode "
    ):

        summary = text.replace(
            "episode ",
            ""
        ).strip()

        memory.add_episode(
            summary
        )

        print(
            "Episode stored."
        )

        return
    
    if text == "episodes":

        episodes = (
            memory.get_recent_episodes()
        )

        for episode in episodes:

            print(
                f"{episode['timestamp']} "
                f"- "
                f"{episode['summary']}"
            )

        return

    if text == "context":

        entries = (
            memory.get_recent_context()
        )

        for entry in entries:

            print(
                f"[{entry['role']}] "
                f"{entry['content']}"
            )

        return

    if text == "clear context":

        memory.recent_context.clear()

        print(
            "Context cleared."
        )

        return

    print(
        f"[EVENT] user_input: {text}"
    )

    memory.add_context(
        "user",
        text
    )

    if text.startswith(
        "life event "
    ):

        description = text.replace(
            "life event ",
            ""
        ).strip()

        memory.add_life_event(
            description
        )

        print(
            "Life event stored."
        )

        return
    
    if text == "life events":

        events = (
            memory.get_life_events()
        )

        for event in events:

            print(
                f"{event['timestamp']} "
                f"- "
                f"{event['description']}"
            )

        return

    memory.compress_context()


def main():

    print("=" * 40)
    print("AIYA CORE ENGINE")
    print("=" * 40)

    # Core systems
    
    state_manager = StateManager()

    event_bus = EventBus()

    global service_manager

    service_manager = ServiceManager()

    plugin_manager = PluginManager()

    # Memory

    memory_manager = MemoryManager()

    service_manager.register(
        "memory",
        memory_manager
    )

    context_count = len(
        memory_manager
        .get_recent_context(100)
    )

    print(
        f"Restored "
        f"{context_count} "
        f"context entries."
    )

    # Events

    event_bus.subscribe(
        "engine_started",
        on_engine_started
    )

    event_bus.subscribe(
        "user_input",
        on_user_input
    )

    # Character loading

    character_loader = CharacterLoader()

    character = character_loader.load(
        "characters/Aiya"
    )

    state_manager.set(
        "active_character",
        character
    )

    print(
        f"Loaded Character: {character['name']}"
    )

    # Brain

    brain = Brain(
        state_manager,
        event_bus,
        service_manager
    )

    global brain_instance

    brain_instance = brain

    print("Core systems initialized")

    # Startup event

    event_bus.emit(
        "engine_started"
    )

    print("Engine running")

    # Main loop

    while True:

        command = input("> ")

        if command.lower() in [
            "quit",
            "exit"
        ]:
            break

        event_bus.emit(
            "user_input",
            command
        )



if __name__ == "__main__":
    main()
    
