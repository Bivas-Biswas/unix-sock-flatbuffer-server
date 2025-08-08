import socket
import select
import threading
from concurrent.futures import ThreadPoolExecutor

class Server:
    def __init__(self, host, port, router, max_workers=5):
        self.host = host
        self.port = port
        self.router = router
        self.max_workers = max_workers
        self.server_socket = None
        self.epoll = None
        self.connections = {}
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)

    def start(self):
        """Starts the server and the main event loop."""
        self._setup_socket()
        print(f"[SERVER] Listening on {self.host}:{self.port} with {self.max_workers} workers.")
        try:
            self._event_loop()
        except KeyboardInterrupt:
            print("\n[SERVER] Shutdown signal received.")
        finally:
            self._shutdown()

    def _setup_socket(self):
        """Initializes the main server socket and epoll."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setblocking(False)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(50)

        try:
            self.epoll = select.epoll()
            self.epoll.register(self.server_socket.fileno(), select.EPOLLIN)
        except AttributeError:
            raise RuntimeError("epoll is not available on this system. This code is Linux-specific.")

    def _event_loop(self):
        """The main event loop that polls for I/O events."""
        while True:
            events = self.epoll.poll(1)
            for fileno, event in events:
                if fileno == self.server_socket.fileno():
                    self._accept_connection()
                elif event & select.EPOLLIN:
                    self._handle_request(fileno)

    def _accept_connection(self):
        """Accepts a new client connection."""
        try:
            conn, addr = self.server_socket.accept()
            conn.setblocking(False)
            self.epoll.register(conn.fileno(), select.EPOLLIN)
            self.connections[conn.fileno()] = conn
            print(f"[SERVER] New connection from {addr}")
        except socket.error as e:
            print(f"[SERVER] Error accepting connection: {e}")

    def _handle_request(self, fileno):
        """Handles an incoming request from a client by reading the header."""
        client_socket = self.connections.get(fileno)
        if not client_socket:
            return

        try:
            header_data = client_socket.recv(1024)
            if header_data:
                self._process_header(fileno, client_socket, header_data)
            else:
                print(f"[SERVER] Client at fileno {fileno} disconnected.")
                self._close_connection(fileno)
        except Exception as e:
            print(f"[SERVER] Error handling request from fileno {fileno}: {e}")
            self._close_connection(fileno)

    def _process_header(self, fileno, client_socket, header_data):
        """Parses the header and submits the task to the thread pool."""
        header_str = header_data.decode('utf-8').strip()
        print(f"[SERVER] Received header: {header_str}")
        
        try:
            parts = dict(item.split("=") for item in header_str.split(","))
            label = parts.get('label')
            length = int(parts.get('length', 0))
        except (ValueError, TypeError):
            print(f"[SERVER] Invalid header format: {header_str}")
            self._close_connection(fileno)
            return

        handler = self.router.get_handler(label)
        if handler and length > 0:
            # Unregister from epoll; worker now owns the socket
            self.epoll.unregister(fileno)
            del self.connections[fileno]
            
            print(f"[SERVER] Submitting task for '{label}' to thread pool.")
            self.thread_pool.submit(self._worker_task, handler, client_socket, length)
        else:
            print(f"[SERVER] No handler for label '{label}' or invalid length. Closing.")
            self._close_connection(fileno)
            
    @staticmethod 
    def _worker_task(self, handler, client_socket, payload_length):
        """The task run by the worker thread. It receives data, calls the handler, and sends the response."""
        try:
            client_socket.setblocking(True)
            payload = client_socket.recv(payload_length)
            if payload:
                # Call the specific handler function (e.g., handle_echo)
                response = handler(client_socket, payload)
                if response:
                    client_socket.sendall(response)
        except Exception as e:
            print(f"[WORKER {threading.get_ident()}] Error during task execution: {e}")
        finally:
            client_socket.close()

    def _close_connection(self, fileno):
        """Closes a client connection and cleans up resources."""
        if fileno in self.connections:
            print(f"[SERVER] Closing connection for fileno {fileno}")
            self.epoll.unregister(fileno)
            self.connections[fileno].close()
            del self.connections[fileno]

    def _shutdown(self):
        """Shuts down the server gracefully."""
        self.thread_pool.shutdown(wait=True)
        self.epoll.close()
        self.server_socket.close()
        print("[SERVER] Shutdown complete.")
