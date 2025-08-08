import socket
import time

# --- Configuration ---
HOST = '127.0.0.1'
PORT = 65432
HEADER_FORMAT = "label={label},length={length}"

def send_request(label, payload):
    """
    Connects to the server, sends a request, and prints the response.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            print(f"\n--- Sending request with label '{label}' ---")

            # 1. Prepare and send the header
            payload_bytes = payload.encode('utf-8')
            header = HEADER_FORMAT.format(label=label, length=len(payload_bytes))
            print(f"Client: Sending header -> {header}")
            s.sendall(header.encode('utf-8'))

            # A small delay to ensure the server's main thread processes the header
            # before the payload arrives. In a real high-performance scenario,
            # the server should be able to handle this without a delay.
            time.sleep(0.1)

            # 2. Send the actual payload
            print(f"Client: Sending payload -> {payload}")
            s.sendall(payload_bytes)

            # 3. Wait for and receive the response
            response = s.recv(1024)
            print(f"Client: Received response -> {response.decode('utf-8')}")

        except ConnectionRefusedError:
            print("Connection refused. Is the server running?")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Example 1: Send a message to be reversed
    send_request('REVERSE', 'Hello, World!')

    # Wait a moment before the next request
    time.sleep(1)

    # Example 2: Send a message to be echoed
    send_request('ECHO', 'This is a test message.')

    # Example 3: Send another message to be reversed
    time.sleep(1)
    send_request('REVERSE', 'Python Epoll Server')
