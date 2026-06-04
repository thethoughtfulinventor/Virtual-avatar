import subprocess
import shutil
from tools.base_tool import BaseTool

# Ordered by likelihood of being installed.
# Covers KDE, GNOME, XFCE, and standalone emulators.
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
    "kgx",           # GNOME Console (newer GNOME)
    "mate-terminal",
    "x-terminal-emulator",  # Debian/Ubuntu generic wrapper
]

_ALIASES: dict[str, str] = {
    "browser":      "firefox",
    "firefox":      "firefox",
    "chrome":       "google-chrome",
    "chromium":     "chromium-browser",
    "files":        "dolphin",
    "file manager": "dolphin",
    "dolphin":      "dolphin",
    "nautilus":     "nautilus",
    "thunar":       "thunar",
    "editor":       "kate",
    "text editor":  "kate",
    "kate":         "kate",
    "gedit":        "gedit",
    "vscode":       "code",
    "vs code":      "code",
    "code":         "code",
    "steam":        "steam",
    "discord":      "discord",
    "spotify":      "spotify",
}

# Terminal aliases
_TERMINAL_ALIASES = frozenset({
    "terminal", "term", "console", "shell", "bash", "zsh",
})


def _find_terminal() -> str | None:
    """
    Returns the first available terminal emulator found
    in PATH, or None if none are installed.

    FIX: added 'x-terminal-emulator' (Debian/Ubuntu) and
    'mate-terminal' to the candidate list; these were
    missing, causing detection failures on common distros.
    """
    for term in _TERMINAL_CANDIDATES:
        if shutil.which(term):
            return term
    return None


class AppLaunchTool(BaseTool):
    """
    Launches a desktop application by name.

    FIX (v2):
    - Terminal detection now uses _find_terminal() correctly
      and reports which candidates were tried on failure.
    - subprocess.Popen now receives a list instead of a
      shell=True string, which is safer and avoids the
      shell layer misinterpreting application names with
      spaces or special chars.
    - Added 'mate-terminal', 'thunar', 'gedit', 'discord',
      'spotify' to the alias table.
    """

    name = "app_launch"
    description = (
        "Launches a desktop application by name. "
        "Use when the user asks to open or start "
        "an app. "
        "Args: app (str) — app name or command."
    )

    def run(self, args: dict, context: dict) -> str:
        app = args.get("app", "").strip()
        if not app:
            return "No application specified."

        app_lower = app.lower()

        # --- Resolve command ---
        if app_lower in _TERMINAL_ALIASES:
            command = _find_terminal()
            if not command:
                tried = ", ".join(_TERMINAL_CANDIDATES)
                return (
                    f"No terminal emulator found. "
                    f"Tried: {tried}\n"
                    f"Install one with: "
                    f"sudo apt install xterm"
                )
        else:
            command = _ALIASES.get(app_lower, app)
            # Check only the base binary name
            base_cmd = command.split()[0]
            if not shutil.which(base_cmd):
                return (
                    f"Application not found: '{base_cmd}'. "
                    f"Is it installed and on PATH?"
                )

        # --- Launch ---
        # FIX: pass command as a list, not shell=True string.
        # For multi-word commands (e.g. "google-chrome --incognito")
        # we still split on whitespace.
        cmd_parts = command.split() if isinstance(command, str) else [command]

        try:
            subprocess.Popen(
                cmd_parts,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,  # detach from parent process
            )
            return f"Launched: {command}"

        except FileNotFoundError:
            return f"Could not find executable: '{cmd_parts[0]}'"

        except Exception as e:
            return f"Failed to launch '{app}': {e}"