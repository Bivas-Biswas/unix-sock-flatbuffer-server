import socket
import select
import threading
import os
from concurrent.futures import ThreadPoolExecutor

from MyServer.Payloads.Root import Root

class Server:
    FILE_IDENTIFIER = b'PLDE'
    HEADER_SIZE = 8 # 4 bytes for identifier + 4 bytes for payload length

    def __init__(self, sock_path, router, max_workers=5):
        self.sock_path = sock_path
        self.router = router
        self.max_workers = max_workers
        self.server_socket = None
        self.epoll = None
        self.connections = {}
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)

    def start(self):
        try:
            if os.path.exists(self.sock_path):
                os.remove(self.sock_path)
        except OSError as e:
            print(f"[SERVER] Error removing socket file: {e}")
            return
        
        self._setup_socket()
        print(f"[SERVER] Listening on {self.sock_path} with {self.max_workers} workers.")
        try:
            self._event_loop()
        except KeyboardInterrupt:
            print("\n[SERVER] Shutdown signal received.")
        finally:
            self._shutdown()

    def _setup_socket(self):
        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setblocking(False)
        self.server_socket.bind(self.sock_path)
        self.server_socket.listen(50)
        self.epoll = select.epoll()
        self.epoll.register(self.server_socket.fileno(), select.EPOLLIN)

    def _event_loop(self):
        while True:
            events = self.epoll.poll(1)
            for fileno, event in events:
                if fileno == self.server_socket.fileno():
                    self._accept_connection()
                elif event & select.EPOLLIN:
                    # For FlatBuffers, we'll read the header and payload in the worker
                    # to simplify the main loop. We just hand off the socket.
                    client_socket = self.connections.get(fileno)
                    if client_socket:
                        self.epoll.unregister(fileno)
                        del self.connections[fileno]
                        self.thread_pool.submit(Server._worker_task, self.router, client_socket)


    def _accept_connection(self):
        conn, addr = self.server_socket.accept()
        conn.setblocking(False)
        self.epoll.register(conn.fileno(), select.EPOLLIN)
        self.connections[conn.fileno()] = conn
        print(f"[SERVER] New connection from {addr}")

    @staticmethod
    def _worker_task(router, client_socket):
        """Worker task now reads the entire message, decodes FlatBuffer, and routes."""
        try:
            client_socket.setblocking(True)
            
            # 1. Read the fixed-size header (identifier + length)
            header = client_socket.recv(Server.HEADER_SIZE)
            if not header or len(header) < Server.HEADER_SIZE:
                print(f"[WORKER {threading.get_ident()}] Failed to receive full header.")
                return

            # 2. Verify the file identifier and get payload length
            identifier = header[:4]
            if identifier != Server.FILE_IDENTIFIER:
                print(f"[WORKER {threading.get_ident()}] Invalid File Identifier: {identifier}")
                return
            
            payload_len = int.from_bytes(header[4:], 'little')

            # 3. Read the FlatBuffer payload
            payload_buf = client_socket.recv(payload_len)
            if not payload_buf:
                return

            # 4. Decode the FlatBuffer
            root = Root.GetRootAsRoot(payload_buf, 0)
            payload_type = root.PayloadType()
            
            handler = router.get_handler(payload_type)
            if not handler:
                print(f"[WORKER {threading.get_ident()}] No handler for payload type {payload_type}")
                return

            # 5. Get the actual payload table from the union
            union_payload = root.Payload()
            if union_payload:
                # Call the specific handler function (e.g., handle_echo)
                response = handler(client_socket, union_payload)
                if response:
                    client_socket.sendall(response)

        except Exception as e:
            print(f"[WORK_IDENTIFIER] {threading.get_ident()}] Error during task execution: {e}")
        finally:
            client_socket.close()

    def _shutdown(self):
        self.thread_pool.shutdown(wait=True)
        self.epoll.close()
        self.server_socket.close()
        print("[SERVER] Shutdown complete.")
