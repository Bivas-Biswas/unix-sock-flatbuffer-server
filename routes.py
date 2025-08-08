class Router:
    def __init__(self):
        self._routes = {}

    def register(self, label, handler):
        """Registers a new handler for a given label."""
        print(f"[ROUTER] Registering handler for '{label}'")
        self._routes[label] = handler

    def get_handler(self, label):
        """Retrieves the handler for a given label."""
        return self._routes.get(label)