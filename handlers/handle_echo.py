import threading
import socket

def handle_echo(client_socket, payload):
    """
    Handles the ECHO feature.
    Receives the client socket and the payload, returns the response bytes.
    """
    print(f"[WORKER {threading.get_ident()}] Echoing {len(payload)} bytes.")
    return b"ECHO: " + payload