import subprocess
from tools.base_tool import BaseTool

_BLOCKED = [
    "rm -rf",
    "rm -r /",
    "mkfs",
    "dd if=",
    "dd of=",
    ":(){:|:&};:",
    "shutdown",
    "reboot",
    "halt",
    "init 0",
    "init 6",
]

_TIMEOUT = 10


class TerminalRunTool(BaseTool):
    """
    Runs a shell command and returns output.

    Use when the user asks to run a command,
    check a process, read a log, or perform
    any terminal operation.
    """

    name = "terminal_run"
    description = (
        "Runs a shell command and returns output. "
        "Use for system queries, running scripts, "
        "checking processes, or terminal tasks. "
        "Args: command (str) — shell command to run."
    )

    def run(self, args, context):

        command = args.get("command", "").strip()

        if not command:
            return "No command provided."

        cmd_lower = command.lower()

        for pattern in _BLOCKED:
            if pattern in cmd_lower:
                return (
                    f"Blocked for safety: "
                    f"'{pattern}' is not permitted."
                )

        try:

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=_TIMEOUT
            )

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if stdout and stderr:
                return f"{stdout}\n[stderr: {stderr}]"

            if stdout:
                return stdout

            if stderr:
                return f"[stderr: {stderr}]"

            return "(command ran with no output)"

        except subprocess.TimeoutExpired:
            return (
                f"Timed out after {_TIMEOUT}s."
            )

        except Exception as e:
            return f"Command failed: {e}"