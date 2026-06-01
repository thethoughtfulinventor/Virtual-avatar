import requests

from llm.model_config import ModelConfig


class OllamaClient:

    def __init__(self, model=None):

        self.model = (
            model or ModelConfig.MODEL
        )

        self.url = ModelConfig.URL

        self.timeout = ModelConfig.TIMEOUT

    def chat(
        self,
        system_prompt,
        messages
    ):
        """
        Send a chat request to Ollama.

        system_prompt: str
            Full character and context prompt.

        messages: list of dicts
            [{"role": "user"/"assistant",
              "content": str}, ...]

        Returns the model's reply as a string,
        or an empty string on failure.
        """

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                *messages
            ],
            "stream": False
        }

        try:

            response = requests.post(
                self.url,
                json=payload,
                timeout=self.timeout
            )

        except Exception as e:

            print(f"[LLM] Connection error: {e}")

            return ""

        if response.status_code != 200:

            print(
                f"[LLM] Error {response.status_code}: "
                f"{response.text}"
            )

            return ""

        data = response.json()

        return (
            data
            .get("message", {})
            .get("content", "")
            .strip()
        )