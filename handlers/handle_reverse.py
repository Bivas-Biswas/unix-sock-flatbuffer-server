import threading
import socket

def handle_reverse(client_socket, payload):
    """
    Handles the REVERSE feature.
    Receives the client socket and the payload, returns the response bytes.
    """
    print(f"[WORKER {threading.get_ident()}] Reversing {len(payload)} bytes.")
    # This simulates a CPU-bound task.
    return b"REVERSED: " + payload[::-1]