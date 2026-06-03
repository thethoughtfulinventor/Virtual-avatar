import subprocess
import shutil
from tools.base_tool import BaseTool

_ALIASES = {
    "terminal":     "konsole",
    "browser":      "firefox",
    "firefox":      "firefox",
    "chrome":       "google-chrome",
    "chromium":     "chromium-browser",
    "files":        "dolphin",
    "file manager": "dolphin",
    "dolphin":      "dolphin",
    "nautilus":     "nautilus",
    "editor":       "kate",
    "text editor":  "kate",
    "kate":         "kate",
    "vscode":       "code",
    "vs code":      "code",
    "code":         "code",
    "steam":        "steam",
}


class AppLaunchTool(BaseTool):
    """
    Launches a desktop application.

    Use when the user asks to open or
    launch an application by name.
    """

    name = "app_launch"
    description = (
        "Launches a desktop application by name. "
        "Use when the user asks to open or start "
        "an app. "
        "Args: app (str) — app name or command."
    )

    def run(self, args, context):

        app = args.get("app", "").strip()

        if not app:
            return "No application specified."

        command = _ALIASES.get(app.lower(), app)
        base_cmd = command.split()[0]

        if not shutil.which(base_cmd):
            return (
                f"Not found: '{base_cmd}'. "
                f"Is it installed?"
            )

        try:

            subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            return f"Launched: {command}"

        except Exception as e:
            return f"Failed to launch '{app}': {e}"