from memory.user_profile import UserProfile
from memory.project_manager import ProjectManager
from memory.episodic_memory import EpisodicMemory
from memory.recent_context import RecentContext
from memory.life_events import LifeEvents

class MemoryManager:

    def __init__(self):

        self.user_profile = UserProfile()

        self.project_manager = (
            ProjectManager()
        )
        
        self.episodic_memory = (
    		EpisodicMemory()
	    )

        self.life_events = (
            LifeEvents()
        )

        self.recent_context = (
            RecentContext()
        )  

    # User Profile Memory

    def remember(
        self,
        key,
        value
    ):

        self.user_profile.set_fact(
            key,
            value
        )

    def recall(
        self,
        key
    ):

        return self.user_profile.get_fact(
            key
        )

    # Project Memory

    def create_project(
        self,
        name
    ):

        self.project_manager.create_project(
            name
        )

    def get_project(
        self,
        name
    ):

        return self.project_manager.get_project(
            name
        )

    def list_projects(
        self
    ):

        return (
            self.project_manager
            .list_projects()
        )
    
    def add_episode(
        self,
        summary
    ):

        self.episodic_memory.add_episode(
            summary
        )


    def get_recent_episodes(
        self,
        count=10
    ):

        return (
            self.episodic_memory
            .get_recent(count)
        )
    
    def add_context(
        self,
        role,
        content
    ):

        self.recent_context.add(
            role,
            content
        )


    def get_recent_context(
        self,
        count=10
    ):

        return (
            self.recent_context
            .get_recent(count)
        )

    def compress_context(self):

        entries = self.recent_context.get_recent(5)

        if len(entries) < 5:
            return

        summary = (
            f"Conversation contained "
            f"{len(entries)} messages."
        )

        self.add_episode(summary)

        self.recent_context.entries = (
            self.recent_context.entries[-2:]
        )

        self.recent_context.save()
    
    def add_life_event(
        self,
        description
    ):

        self.life_events.add_event(
            description
        )


    def get_life_events(
        self
    ):

        return (
            self.life_events.get_events()
        )