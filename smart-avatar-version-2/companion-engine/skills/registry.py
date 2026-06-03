from skills.web_search_skill import WebSearchTool
from skills.file_skill import (
    FileListTool,
    FileReadTool,
    FileWriteTool,
    FileDeleteTool,
    FolderCreateTool,
    FolderDeleteTool,
)
from skills.terminal_skill import TerminalRunTool
from skills.app_launcher_skill import AppLaunchTool
from skills.system_skill import SystemStatsTool


SKILL_CLASSES = [
    WebSearchTool,
    FileListTool,
    FileReadTool,
    FileWriteTool,
    FileDeleteTool,
    FolderCreateTool,
    FolderDeleteTool,
    TerminalRunTool,
    AppLaunchTool,
    SystemStatsTool,
]


def register_skills(tool_registry):

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