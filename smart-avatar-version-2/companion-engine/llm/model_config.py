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

    # --------------------------------------------------
    # GPU / CUDA settings
    # --------------------------------------------------

    # Minimum free VRAM (MB) to attempt full GPU offload.
    # CudaManager will warn at startup if available VRAM
    # is below this threshold.
    # qwen3:8b at Q4_K_M requires ~5 GB; leave headroom
    # for the OS and other processes.
    MIN_VRAM_MB = 5120

    # Number of model layers to offload to GPU.
    # None = let Ollama auto-detect (strongly recommended).
    # Override only if Ollama makes a poor choice for your
    # specific GPU/model combination.
    # Example: GPU_LAYERS = 35  (full offload for 8B models
    # on cards with 8+ GB VRAM)
    GPU_LAYERS: int | None = None