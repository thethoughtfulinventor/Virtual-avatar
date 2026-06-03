import subprocess
import shutil
from tools.base_tool import BaseTool

# Ordered by likelihood of being installed
_TERMINAL_CANDIDATES = [
    "konsole",
    "gnome-terminal",
    "xfce4-terminal",
    "xterm",
    "alacritty",
    "kitty",
    "tilix",
    "terminator",
    "lxterminal",
    "urxvt",
    "rxvt",
    "ptyxis",
    "kgx",
]

_ALIASES = {
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


def _find_terminal():
    """Returns the first available terminal emulator."""
    for term in _TERMINAL_CANDIDATES:
        if shutil.which(term):
            return term
    return None


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

        app_lower = app.lower()

        # Terminal gets special dynamic detection
        if app_lower in ("terminal", "term",
                         "console", "shell"):
            command = _find_terminal()
            if not command:
                return (
                    "No terminal emulator found. "
                    "Tried: "
                    + ", ".join(_TERMINAL_CANDIDATES)
                )

        else:
            command = _ALIASES.get(app_lower, app)
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