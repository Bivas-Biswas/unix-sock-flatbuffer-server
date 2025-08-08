class Router:
    def __init__(self):
        self._routes = {}

    def register(self, payload_type, handler):
        """Registers a handler for a specific FlatBuffers payload type."""
        print(f"[ROUTER] Registering handler for type '{payload_type}'")
        self._routes[payload_type] = handler

    def get_handler(self, payload_type):
        """Retrieves the handler for a given payload type."""
        return self._routes.get(payload_type)