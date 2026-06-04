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

    # --------------------------------------------------
    # User Profile Memory
    # --------------------------------------------------

    def remember(self, key, value):

        self.user_profile.set_fact(key, value)

    def recall(self, key):

        return self.user_profile.get_fact(key)

    # --------------------------------------------------
    # Project Memory
    # --------------------------------------------------

    def create_project(self, name):

        self.project_manager.create_project(name)

    def get_project(self, name):

        return self.project_manager.get_project(name)

    def list_projects(self):

        return self.project_manager.list_projects()

    # --------------------------------------------------
    # Episodic Memory
    # --------------------------------------------------

    def add_episode(self, summary):

        self.episodic_memory.add_episode(summary)

    def get_recent_episodes(self, count=10):

        return self.episodic_memory.get_recent(count)

    # --------------------------------------------------
    # Recent Context
    # --------------------------------------------------

    def add_context(self, role, content, character=None):

        self.recent_context.add(role, content, character)

    def get_recent_context(self, count=50):

        return self.recent_context.get_recent(count)

    def compress_context(self, summary=None):
        """
        Stores the provided summary as an episode,
        then trims recent context to the last 3 entries.

        Uses keep_last() instead of direct .entries
        manipulation so this works with both SQL and
        any future backend.

        Returns the entries that were summarized,
        or None if context was too short to compress.
        """

        entries = self.recent_context.get_recent(25)

        if len(entries) < 25:
            return None

        if summary:
            self.add_episode(summary)

        self.recent_context.keep_last(3)

        return entries

    # --------------------------------------------------
    # Life Events
    # --------------------------------------------------

    def add_life_event(self, description):

        self.life_events.add_event(description)

    def get_life_events(self):

        return self.life_events.get_events()