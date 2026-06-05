class PluginManager:
    """
    Phase 1 plugin registry.

    Stores plugins and allows other
    systems to access them.

    Dynamic loading can be added later.
    """

    def __init__(self):
        self.plugins = {}

    def register(self, name, plugin):
        self.plugins[name] = plugin

    def get(self, name):
        return self.plugins.get(name)

    def has(self, name):
        return name in self.plugins

    def remove(self, name):
        if name in self.plugins:
            del self.plugins[name]

    def list_plugins(self):
        return list(self.plugins.keys())
