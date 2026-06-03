class ModelConfig:

    # Ollama model to use
    MODEL = "qwen3:8b"

    # Chat endpoint — supports system prompt
    # and full message history natively
    URL = "http://localhost:11434/api/chat"

    # Request timeout in seconds
    TIMEOUT = 60

    # How many recent context entries
    # to include in each LLM request
    MAX_CONTEXT = 10

    # Phase 6: Run the Planner before each
    # conversational LLM call to route to the
    # best character and pick a response strategy.
    #
    # Adds one extra LLM call per conversation turn.
    # Set to False to disable and reduce latency
    # (manual switching still works either way).
    ENABLE_PLANNER = True