import threading

import MyServer.Payloads.ReverseRequest

def handle_reverse(client_socket, union_payload):
    """
    Handles the REVERSE feature.
    Receives the generic union payload table.
    """
    # FIX: Cast the generic Table object to the specific ReverseRequest type.
    reverse_request = MyServer.Payloads.ReverseRequest.ReverseRequest()
    reverse_request.Init(union_payload.Bytes, union_payload.Pos)

    data_to_reverse = reverse_request.Data().decode('utf-8')
    print(f"[WORKER {threading.get_ident()}] Reversing data: {data_to_reverse}")
    reversed_data = data_to_reverse[::-1]
    return b"REVERSED: " + reversed_data.encode('utf-8')