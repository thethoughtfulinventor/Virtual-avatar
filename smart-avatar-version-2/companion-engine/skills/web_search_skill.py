from tools.base_tool import BaseTool

try:
    from ddgs import DDGS
    _DDGS_AVAILABLE = True
except ImportError:
    _DDGS_AVAILABLE = False

_NEWS_KEYWORDS = {
    "news", "headline", "headlines",
    "latest", "today", "current", "recent",
}


class WebSearchTool(BaseTool):
    """
    Searches the web for current information.

    Use when the user asks about recent
    events, news, weather, prices, sports,
    or any question requiring live data.
    """

    name = "web_search"
    description = (
        "Retrieves information from the internet "
        "for answering questions. "
        "Used for facts, news, weather, research, "
        "sports, prices, and current events. "
        "Does not open browser windows."
    )
    def run(self, args, context):

        if not _DDGS_AVAILABLE:
            return (
                "Web search unavailable. "
                "Run: pip install ddgs"
            )

        query = args.get("query", "").strip()

        if not query:
            return "No search query provided."

        try:

            with DDGS() as ddgs:

                # Use news search for news queries
                if any(
                    w in query.lower()
                    for w in _NEWS_KEYWORDS
                ):

                    results = list(
                        ddgs.news(query, max_results=4)
                    )

                    if results:

                        lines = [
                            f"News results — {query}:"
                        ]

                        for r in results:
                            title = r.get("title", "")
                            body = r.get("body", "")
                            lines.append(
                                f"• {title}: {body}"
                            )

                        return "\n".join(lines)

                # Standard text search
                results = list(
                    ddgs.text(query, max_results=4)
                )

                if not results:
                    return (
                        f"No results found for: {query}"
                    )

                lines = [f"Search results — {query}:"]

                for r in results:
                    title = r.get("title", "")
                    body = r.get("body", "")
                    lines.append(f"• {title}: {body}")

                return "\n".join(lines)

        except Exception as e:
            return f"Web search failed: {e}"