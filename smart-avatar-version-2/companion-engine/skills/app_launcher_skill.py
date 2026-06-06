import configparser
import os
import shutil
import subprocess
from pathlib import Path
from difflib import get_close_matches

from tools.base_tool import BaseTool

_TERMINAL_CANDIDATES = [
    "konsole",
    "gnome-terminal",
    "xfce4-terminal",
    "kitty",
    "alacritty",
    "tilix",
    "terminator",
    "mate-terminal",
    "kgx",
    "ptyxis",
    "x-terminal-emulator",
    "xterm",
]

_ALIASES = {
    "browser": "firefox",
    "web browser": "firefox",
    "chrome": "google-chrome",
    "files": "dolphin",
    "file manager": "dolphin",
    "editor": "kate",
    "text editor": "kate",
    "vs code": "code",
}

_TERMINAL_ALIASES = {
    "a terminal",
    "terminal",
    "console",
    "shell",
    "bash",
    "zsh",
}


def _safe_launch(command):
    subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def _find_terminal():
    for term in _TERMINAL_CANDIDATES:
        if shutil.which(term):
            return term
    return None


class AppLaunchTool(BaseTool):

    name = "app_launch"

    description = (
        "Launch desktop applications using desktop entries, "
        "Flatpak, Snap, PATH binaries, and aliases."
    )

    def __init__(self):
        self.desktop_entries = self._build_desktop_cache()
        self.flatpak_apps = self._build_flatpak_cache()

    # --------------------------------------------------
    # Desktop Entry Discovery
    # --------------------------------------------------

    def _desktop_dirs(self):

        return [
            Path(
                os.environ.get(
                    "XDG_DATA_HOME",
                    str(Path.home() / ".local/share"),
                )
            )
            / "applications",

            Path("/usr/share/applications"),

            Path("/usr/local/share/applications"),

            Path(
                "/var/lib/flatpak/exports/share/applications"
            ),

            Path.home()
            / ".local/share/flatpak/exports/share/applications",

            Path(
                "/var/lib/snapd/desktop/applications"
            ),
        ]

    def _build_desktop_cache(self):

        cache = {}

        for directory in self._desktop_dirs():

            if not directory.exists():
                continue

            for desktop_file in directory.rglob(
                "*.desktop"
            ):

                try:

                    parser = configparser.ConfigParser(
                        interpolation=None
                    )

                    parser.read(
                        desktop_file,
                        encoding="utf-8"
                    )

                    if "Desktop Entry" not in parser:
                        continue

                    section = parser["Desktop Entry"]

                    names = [
                        desktop_file.stem,
                        section.get("Name", ""),
                        section.get(
                            "GenericName",
                            ""
                        ),
                    ]

                    for name in names:

                        name = (
                            name.lower().strip()
                        )

                        if not name:
                            continue

                        cache[name] = desktop_file

                except Exception:
                    continue

        return cache

    # --------------------------------------------------
    # Flatpak Discovery
    # --------------------------------------------------

    def _build_flatpak_cache(self):

        cache = {}

        if not shutil.which("flatpak"):
            return cache

        try:

            result = subprocess.run(
                [
                    "flatpak",
                    "list",
                    "--app",
                    "--columns=application,name",
                ],
                capture_output=True,
                text=True,
            )

            for line in result.stdout.splitlines():

                parts = line.split("\t")

                if len(parts) < 2:
                    continue

                app_id = parts[0].strip()
                name = parts[1].strip()

                cache[name.lower()] = app_id
                cache[app_id.lower()] = app_id

        except Exception:
            pass

        return cache

    # --------------------------------------------------
    # Desktop Launch Methods
    # --------------------------------------------------

    def _launch_with_gtk(self, desktop_file):

        if not shutil.which("gtk-launch"):
            return False

        try:

            _safe_launch(
                [
                    "gtk-launch",
                    desktop_file.stem,
                ]
            )

            return True

        except Exception:
            return False

    def _launch_with_gio(self, desktop_file):

        if not shutil.which("gio"):
            return False

        try:

            _safe_launch(
                [
                    "gio",
                    "launch",
                    str(desktop_file),
                ]
            )

            return True

        except Exception:
            return False

    # --------------------------------------------------
    # Flatpak Launch
    # --------------------------------------------------

    def _launch_flatpak(self, app_name):

        app_name = app_name.lower()

        app_id = self.flatpak_apps.get(
            app_name
        )

        if not app_id:

            matches = get_close_matches(
                app_name,
                self.flatpak_apps.keys(),
                n=1,
                cutoff=0.6
            )

            if matches:
                app_id = self.flatpak_apps[
                    matches[0]
                ]

        if not app_id:
            return False

        try:

            _safe_launch(
                [
                    "flatpak",
                    "run",
                    app_id,
                ]
            )

            return True

        except Exception:
            return False

    # --------------------------------------------------
    # PATH Launch
    # --------------------------------------------------

    def _launch_binary(self, command):

        executable = command.split()[0]

        if not shutil.which(executable):
            return False

        try:

            _safe_launch(command.split())
            return True

        except Exception:
            return False

    # --------------------------------------------------
    # Main Entry
    # --------------------------------------------------

    def run(self, args, context):

        app = args.get("app", "").strip()

        if not app:
            return "No application specified."

        app_lower = app.lower()

        if app_lower in _TERMINAL_ALIASES:

            terminal = _find_terminal()

            if not terminal:
                return (
                    "No terminal emulator found."
                )

            _safe_launch([terminal])

            return (
                f"SUCCESS: terminal: {terminal}"
            )

        app_name = _ALIASES.get(
            app_lower,
            app,
        )

        desktop_file = (
            self._find_desktop_match(
                app_name
            )
        )

        if desktop_file:

            if self._launch_with_gtk(
                desktop_file
            ):
                return (
                    f"SUCCESS: Application {app_name}"
                    " via gtk-launch"
                )

            if self._launch_with_gio(
                desktop_file
            ):
                return (
                    f"SUCCESS: Application {app_name}"
                    " via gio"
                )

        if self._launch_flatpak(
            app_name
        ):
            return (
                f"SUCCESS: Application {app_name}"
                " via Flatpak"
            )

        if self._launch_binary(
            app_name
        ):
            return (
                f"SUCCESS: Application {app_name}"
                " via PATH"
            )

        return (
            f"SUCCESS: Application '{app}' "
            "could not be located."
        )
    
    def _find_desktop_match(self, app_name):

        app_name = app_name.lower()

        match = self.desktop_entries.get(
            app_name
        )

        if match:
            return match

        matches = get_close_matches(
            app_name,
            self.desktop_entries.keys(),
            n=1,
            cutoff=0.6
        )

        if matches:

            print(
                "[AppLaunch] Fuzzy match:"
                f" {app_name} -> {matches[0]}"
            )

            return self.desktop_entries[
                matches[0]
            ]

        return None

