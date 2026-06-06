import urllib.parse
import webbrowser

from tools.base_tool import BaseTool


class BrowserTool(BaseTool):

    name = "browser"

    description = (
        "Opens websites or search pages in the user's "
        "web browser. "
        "Does NOT retrieve information. "
        "Never use this tool for answering questions. "
        "Args: action, url, query"
    )

    def run(self, args, context):

        action = args.get("action")

        if action == "open":

            url = args.get("url", "").strip()

            if not url:
                return "No URL provided."

            if not url.startswith(
                ("http://", "https://")
            ):
                url = f"https://{url}"

            webbrowser.open(url)

            return f"Opened {url}"

        if action == "search":

            query = args.get("query", "").strip()

            if not query:
                return "No search query provided."

            url = (
                "https://www.google.com/search?q="
                + urllib.parse.quote_plus(query)
            )

            webbrowser.open(url)

            return f"Searching for: {query}"

        return "Unknown browser action."