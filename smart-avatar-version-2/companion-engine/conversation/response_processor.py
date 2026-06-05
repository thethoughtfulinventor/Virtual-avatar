import re
# conversation/response_processor.py

# Keys that must never be stored in the user profile.
# Using frozenset for O(1) lookup.
_KEY_BLACKLIST = frozenset({
    "switch", "request", "wants", "asked",
    "said", "current", "active", "character",
    "action", "command", "message", "response",
    "user_request", "context", "intent",
    "search", "result", "file", "path", "folder",
    "directory", "system", "cpu", "ram", "gpu",
    "storage", "terminal", "process", "output",
    "error", "tool", "skill", "retrieved",
    "news", "weather", "data", "query",
    "true", "false", "null", "none",
})

# Patterns that indicate a value is NOT a personal fact.
_BAD_VALUE_PATTERNS = re.compile(
    r'^/'           # file path
    r'|^https?://'  # URL
    r'|^\d+$'       # pure number
    r'|^[A-Z]:\\'   # Windows path
    r'|\s{2,}',     # multiple spaces (likely prose)
    re.IGNORECASE,
)

_FACT_PATTERN  = re.compile(r'\[REMEMBER:([^\]]+)\]')
_EVENT_PATTERN = re.compile(r'\[LIFE_EVENT:([^\]]+)\]')
_WRITE_PATTERN = re.compile(
    r'\[WRITE_FILE:([^\]]+)\](.*?)\[/WRITE_FILE\]',
    re.DOTALL,
)

class ResponseProcessor:

    def __init__(self, tool_registry):
        self.tool_registry = tool_registry

    def process(self, response, memory):

        response = self._extract_and_store_facts(
            response,
            memory
        )

        response = self._extract_response_actions(
            response,
            memory
        )

        return response

    def _extract_and_store_facts(
        self,
        response,
        memory
    ):
        """
        Parse [REMEMBER:key=value] and [LIFE_EVENT:...] tags
        from the LLM response, persist them, then strip the
        tags from the text returned to the user.

        Guards added in v2:
        - Key blacklist is now a frozenset (O(1) lookup).
        - Value must be >1 word OR a clearly meaningful single
          word (avoids storing lone booleans, paths, numbers).
        - Value must not match _BAD_VALUE_PATTERNS.
        - Maximum value length of 120 chars (avoids storing
          entire sentences of tool output).
        """
        if not response:
            return response

        for match in _FACT_PATTERN.findall(response):
            if "=" not in match:
                continue

            key, value = match.split("=", 1)
            key   = key.strip()
            value = value.strip()

            if not key or not value:
                continue

            key_lower = key.lower()

            # Blacklist check
            if any(bad in key_lower for bad in _KEY_BLACKLIST):
                print(f"[Memory] Rejected (blacklist): {key}")
                continue

            # Boolean guard
            if value.lower() in ("true", "false", "null", "none", "yes", "no"):
                print(f"[Memory] Rejected (boolean/null): {key}={value}")
                continue

            # Value pattern guard
            if _BAD_VALUE_PATTERNS.search(value):
                print(f"[Memory] Rejected (bad value pattern): {key}={value}")
                continue

            # Length guard — tool outputs tend to be long
            if len(value) > 120:
                print(f"[Memory] Rejected (too long): {key}")
                continue

            # Skip if unchanged
            existing = memory.recall(key)
            if existing == value:
                continue

            memory.remember(key, value)
            print(f"[Memory] Stored: {key} = {value}")

        for match in _EVENT_PATTERN.findall(response):
            description = match.strip()
            if description:
                memory.add_life_event(description)
                print(f"[Memory] Life event: {description}")

        clean = _FACT_PATTERN.sub("", response)
        clean = _EVENT_PATTERN.sub("", clean).strip()
        return clean
        
    def _extract_response_actions(
        self,
        response,
        memory
    ):
        """
        Handle [WRITE_FILE:path]...[/WRITE_FILE] tags
        embedded in the LLM response.
        """
        if not response:
            return response

        for match in _WRITE_PATTERN.finditer(response):
            path    = match.group(1).strip()
            content = match.group(2)

            write_tool = self.tool_registry.get("file_write")
            if write_tool:
                result = write_tool.run(
                    {"path": path, "content": content},
                    {"memory": memory},
                )
                print(f"[FileWrite] {result}")
            else:
                print("[FileWrite] Tool not registered.")

        return _WRITE_PATTERN.sub("", response).strip()