import MyServer.Payloads.AnyPayload
from server import Server
from handlers import handle_echo, handle_reverse

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

SOCKET_PATH = "/tmp/my_server.sock";

if __name__ == "__main__":
    app_router = Router()

    # Register handlers using the payload type from the generated code
    app_router.register(MyServer.Payloads.AnyPayload.AnyPayload.EchoRequest, handle_echo)
    app_router.register(MyServer.Payloads.AnyPayload.AnyPayload.ReverseRequest, handle_reverse)

    server = Server(SOCKET_PATH, app_router, max_workers=5)
    server.start()
