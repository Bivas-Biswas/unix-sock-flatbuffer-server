import socket
import flatbuffers

# --- Import Generated FlatBuffers Code ---
import MyServer.Payloads.Root
import MyServer.Payloads.AnyPayload
import MyServer.Payloads.EchoRequest
import MyServer.Payloads.ReverseRequest

# --- Configuration ---
HOST = '127.0.0.1'
PORT = 65432
# FIX: File identifier must be exactly 4 bytes.
FILE_IDENTIFIER = b'PLDE' # Must match the server and schema

def create_echo_payload(builder, message):
    """Creates a FlatBuffer payload for an ECHO request."""
    msg_str = builder.CreateString(message)
    MyServer.Payloads.EchoRequest.EchoRequestStart(builder)
    MyServer.Payloads.EchoRequest.EchoRequestAddMessage(builder, msg_str)
    return MyServer.Payloads.EchoRequest.EchoRequestEnd(builder)

def create_reverse_payload(builder, data):
    """Creates a FlatBuffer payload for a REVERSE request."""
    data_str = builder.CreateString(data)
    MyServer.Payloads.ReverseRequest.ReverseRequestStart(builder)
    MyServer.Payloads.ReverseRequest.ReverseRequestAddData(builder, data_str)
    return MyServer.Payloads.ReverseRequest.ReverseRequestEnd(builder)

def send_request(builder, payload_type, payload_offset):
    """Builds the final FlatBuffer, sends it, and waits for a response."""
    # The builder from the main block is used here, not a new one.

    # Build the root object containing the union
    MyServer.Payloads.Root.RootStart(builder)
    MyServer.Payloads.Root.RootAddPayloadType(builder, payload_type)
    MyServer.Payloads.Root.RootAddPayload(builder, payload_offset)
    root = MyServer.Payloads.Root.RootEnd(builder)

    # Finish the buffer, adding the file identifier
    # FIX: Pass the 4-byte identifier directly. It must be bytes, not str.
    builder.Finish(root, FILE_IDENTIFIER)
    
    buf = builder.Output()
    payload_len = len(buf)

    # Create the full message: identifier + length + payload
    # Length is a 4-byte little-endian integer
    full_message = FILE_IDENTIFIER + payload_len.to_bytes(4, 'little') + buf

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            print(f"\n--- Sending request of type {payload_type} ---")
            print(f"Client: Sending {len(full_message)} bytes total.")
            s.sendall(full_message)

            response = s.recv(1024)
            print(f"Client: Received response -> {response.decode('utf-8')}")
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    # Example 1: Send an ECHO request
    # Create one builder for the entire operation.
    builder_echo = flatbuffers.Builder(1024)
    echo_offset = create_echo_payload(builder_echo, "Hello, FlatBuffers!")
    # Pass the builder into the send_request function.
    send_request(builder_echo, MyServer.Payloads.AnyPayload.AnyPayload.EchoRequest, echo_offset)

    # Example 2: Send a REVERSE request
    # Create a new builder for the second, independent operation.
    builder_reverse = flatbuffers.Builder(1024)
    reverse_offset = create_reverse_payload(builder_reverse, "This should be reversed")
    # Pass this new builder into the send_request function.
    send_request(builder_reverse, MyServer.Payloads.AnyPayload.AnyPayload.ReverseRequest, reverse_offset)
