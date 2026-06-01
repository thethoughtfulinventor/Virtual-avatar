class ModelConfig:

    # Ollama model to use
    MODEL = "llama3"

    # Chat endpoint — supports system prompt
    # and full message history natively
    URL = "http://localhost:11434/api/chat"

    # Request timeout in seconds
    TIMEOUT = 60

    # How many recent context entries
    # to include in each LLM request
    MAX_CONTEXT = 10