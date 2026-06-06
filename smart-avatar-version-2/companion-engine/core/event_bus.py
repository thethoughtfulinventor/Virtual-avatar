class EventBus:

    def __init__(self):
        self.listeners = {}

    def subscribe(self, event_name, callback):
        self.listeners.setdefault(
            event_name,
            []
        ).append(callback)

    def unsubscribe(
        self,
        event_name,
        callback
    ):
        if event_name not in self.listeners:
            return

        if callback in self.listeners[event_name]:
            self.listeners[event_name].remove(
                callback
            )

    def emit(
        self,
        event_name,
        **data
    ):
        for callback in self.listeners.get(
            event_name,
            []
        ):
            try:
                callback(**data)

            except Exception as e:
                print(
                    f"[EventBus] "
                    f"Listener error in "
                    f"'{event_name}': {e}"
                )