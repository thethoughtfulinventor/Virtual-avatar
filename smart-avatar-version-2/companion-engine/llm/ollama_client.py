import requests

class OllamaClient:
    def __init__(self, model="llama3"):
        self.model = model
        self.url = "http://localhost:11434/api/generate"

    def generate(self, prompt):
        print("\n[LLM] Sending prompt:")
        print(prompt)

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(self.url, json=payload, timeout=60)
        except Exception as e:
            print("[LLM] Request failed:", e)
            return ""

        print("[LLM] Status:", response.status_code)

        if response.status_code != 200:
            print("[LLM] Error response:", response.text)
            return ""

        data = response.json()

        print("[LLM] Raw response:", data)

        return data.get("response", "")
