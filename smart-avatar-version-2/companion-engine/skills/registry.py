"""
Phase 7 Skill Registry.

Loads all skill modules and registers
their tools into the ToolRegistry.

To add a new skill:
1. Create the file under skills/
2. Import it here and add to SKILL_CLASSES.
"""

from skills.web_search_skill import WebSearchTool
from skills.file_skill import (
    FileListTool,
    FileReadTool,
    FileWriteTool,
)
from skills.terminal_skill import TerminalRunTool
from skills.app_launcher_skill import AppLaunchTool
from skills.system_skill import SystemStatsTool


SKILL_CLASSES = [
    WebSearchTool,
    FileListTool,
    FileReadTool,
    FileWriteTool,
    TerminalRunTool,
    AppLaunchTool,
    SystemStatsTool,
]


def register_skills(tool_registry):
    """
    Instantiate and register all Phase 7 skills
    into the provided ToolRegistry.
    """

    count = 0

    for cls in SKILL_CLASSES:

        try:

            tool_registry.register(cls())
            count += 1

        except Exception as e:

            print(
                f"[Skills] Failed to load "
                f"{cls.__name__}: {e}"
            )

    print(f"[Skills] {count} skills registered.")