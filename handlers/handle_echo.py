import threading

# FIX: Import the module itself, not the class from within it.
# This makes the reference unambiguous.
import MyServer.Payloads.EchoRequest

def handle_echo(client_socket, union_payload):
    """
    Handles the ECHO feature.
    Receives the generic union payload table from the server.
    """
    # FIX: Use the full, explicit path to the EchoRequest class.
    echo_request = MyServer.Payloads.EchoRequest.EchoRequest()
    echo_request.Init(union_payload.Bytes, union_payload.Pos)
    
    message = echo_request.Message().decode('utf-8')
    print(f"[WORKER {threading.get_ident()}] Echoing message: {message}")
    return b"ECHO: " + message.encode('utf-8')
