import os
import shutil
from tools.base_tool import BaseTool

_HOME = os.path.expanduser("~")
_READ_LIMIT = 4000


def _safe_path(raw_path):
    """
    Resolves and validates a path.
    Ensures it stays inside the home dir.
    Fixes the startswith prefix collision bug
    (e.g. /home/patricko matching /home/patrick).
    """
    expanded = os.path.expanduser(raw_path.strip())
    resolved = os.path.realpath(expanded)

    if not (
        resolved == _HOME
        or resolved.startswith(_HOME + os.sep)
    ):
        return None

    return resolved


class FileListTool(BaseTool):
    """
    Lists files and folders in a directory.

    Use when the user asks what's inside
    a folder or wants to browse a directory.
    """

    name = "file_list"
    description = (
        "Lists files and folders in a directory. "
        "Use when the user asks what's inside a "
        "folder. Args: path (str) — directory to "
        "list. Defaults to home dir."
    )

    def run(self, args, context):

        path = args.get("path", "~").strip()
        safe = _safe_path(path)

        if not safe:
            return (
                "Access denied: path escapes "
                "the home directory."
            )

        if not os.path.exists(safe):
            return f"Path not found: {path}"

        if not os.path.isdir(safe):
            return f"Not a directory: {path}"

        try:

            entries = sorted(os.listdir(safe))

            if not entries:
                return f"{safe} is empty."

            lines = [f"Contents of {safe}:"]

            for entry in entries:

                full = os.path.join(safe, entry)
                tag = "/" if os.path.isdir(full) else ""
                lines.append(f"  {entry}{tag}")

            return "\n".join(lines)

        except PermissionError:
            return f"Permission denied: {safe}"


class FileReadTool(BaseTool):
    """
    Reads the contents of a text file.

    Use when the user wants to view the
    contents of a specific file.
    """

    name = "file_read"
    description = (
        "Reads and returns the contents of a "
        "text file. Use when the user asks to "
        "see or read a file. "
        f"Args: path (str). Max {_READ_LIMIT} chars."
    )

    def run(self, args, context):

        path = args.get("path", "").strip()

        if not path:
            return "No file path provided."

        safe = _safe_path(path)

        if not safe:
            return (
                "Access denied: path escapes "
                "the home directory."
            )

        if not os.path.exists(safe):
            return f"File not found: {path}"

        if not os.path.isfile(safe):
            return f"Not a file: {path}"

        try:

            with open(
                safe, "r", errors="replace"
            ) as f:
                content = f.read(_READ_LIMIT)

            if len(content) == _READ_LIMIT:
                content += "\n[... truncated ...]"

            return content

        except PermissionError:
            return f"Permission denied: {safe}"

        except Exception as e:
            return f"Could not read file: {e}"


class FileWriteTool(BaseTool):
    """
    Writes text content to a file.

    Use when the user asks to create or
    save a file with specific content.
    """

    name = "file_write"
    description = (
        "Writes text to a file, overwriting if "
        "it already exists. Args: path (str) — "
        "full file path, content (str) — the "
        "complete actual text to write."
    )

    def run(self, args, context):

        path = args.get("path", "").strip()
        content = args.get("content", "")

        if not path:
            return "No file path provided."

        safe = _safe_path(path)

        if not safe:
            return (
                "Access denied: path escapes "
                "the home directory."
            )

        try:

            parent = os.path.dirname(safe)

            if parent:
                os.makedirs(parent, exist_ok=True)

            with open(safe, "w") as f:
                f.write(content)

            return f"Written: {safe}"

        except PermissionError:
            return f"Permission denied: {safe}"

        except Exception as e:
            return f"Could not write file: {e}"


class FileDeleteTool(BaseTool):
    """
    Deletes a single file.

    Use when the user asks to delete
    or remove a specific file.
    """

    name = "file_delete"
    description = (
        "Deletes a single file. "
        "Args: path (str) — path to the file."
    )

    def run(self, args, context):

        path = args.get("path", "").strip()

        if not path:
            return "No file path provided."

        safe = _safe_path(path)

        if not safe:
            return "Access denied."

        if not os.path.exists(safe):
            return f"File not found: {path}"

        if not os.path.isfile(safe):
            return f"Not a file: {path}"

        try:
            os.remove(safe)
            return f"Deleted: {safe}"

        except PermissionError:
            return f"Permission denied: {safe}"

        except Exception as e:
            return f"Could not delete: {e}"


class FolderCreateTool(BaseTool):
    """
    Creates a new directory.

    Use when the user asks to create
    a folder or directory.
    """

    name = "folder_create"
    description = (
        "Creates a new directory (and any needed "
        "parent dirs). Args: path (str) — "
        "directory path to create."
    )

    def run(self, args, context):

        path = args.get("path", "").strip()

        if not path:
            return "No path provided."

        safe = _safe_path(path)

        if not safe:
            return "Access denied."

        try:
            os.makedirs(safe, exist_ok=True)
            return f"Created: {safe}"

        except PermissionError:
            return f"Permission denied: {safe}"

        except Exception as e:
            return f"Could not create folder: {e}"


class FolderDeleteTool(BaseTool):
    """
    Deletes a folder and all its contents.

    Use when the user asks to delete a
    directory, including non-empty ones.
    """

    name = "folder_delete"
    description = (
        "Deletes a folder and everything inside "
        "it recursively. Args: path (str) — "
        "directory to delete."
    )

    def run(self, args, context):

        path = args.get("path", "").strip()

        if not path:
            return "No path provided."

        safe = _safe_path(path)

        if not safe:
            return "Access denied."

        if not os.path.exists(safe):
            return f"Path not found: {path}"

        if not os.path.isdir(safe):
            return f"Not a directory: {path}"

        try:
            shutil.rmtree(safe)
            return f"Deleted: {safe}"

        except PermissionError:
            return f"Permission denied: {safe}"

        except Exception as e:
            return f"Could not delete folder: {e}"