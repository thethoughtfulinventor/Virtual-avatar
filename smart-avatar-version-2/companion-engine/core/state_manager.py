class StateManager:
    def __init__(self, event_bus=None):
        self.state = {}
        self.event_bus = event_bus

    def get(self, key, default=None):
        return self.state.get(key, default)

    def set(self, key, value):
        old_value = self.state.get(key)

        self.state[key] = value

        if self.event_bus:
            self.event_bus.emit(
                "state_changed",
                key=key,
                old_value=old_value,
                new_value=value
            )