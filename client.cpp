#include <iostream>
#include <string>
#include <vector>
#include <stdexcept>

// Standard C headers for socket programming (Linux/macOS)
#include <sys/socket.h>
#include <unistd.h>
#include <sys/un.h>

// Include the generated FlatBuffers header
#include "schema_generated.h"

// Configuration
const char* SOCKET_PATH = "/tmp/my_server.sock";

// Must match the 4-byte identifier in the server and schema
const char* FILE_IDENTIFIER = "PLDE";

// Forward declaration
void send_request(flatbuffers::FlatBufferBuilder& builder);

int main() {
    try {
        // --- Example 1: Send an ECHO request ---
        {
            flatbuffers::FlatBufferBuilder builder(1024);

            // Create the payload for the EchoRequest
            auto msg = builder.CreateString("Hello from C++!");
            auto echo_payload = MyServer::Payloads::CreateEchoRequest(builder, msg);

            // Create the root object with the union
            // FIX: Use '::' for C++ namespaces
            auto root = MyServer::Payloads::CreateRoot(
                builder,
                MyServer::Payloads::AnyPayload_EchoRequest, // Set the union type
                echo_payload.Union() // Get the offset to the payload
            );

            builder.Finish(root, FILE_IDENTIFIER);
            send_request(builder);
        }

        // --- Example 2: Send a REVERSE request ---
        {
            flatbuffers::FlatBufferBuilder builder(1024);

            // Create the payload for the ReverseRequest
            auto data = builder.CreateString("This should be reversed by the server");
            auto reverse_payload = MyServer::Payloads::CreateReverseRequest(builder, data);

            // Create the root object with the union
            // FIX: Use '::' for C++ namespaces
            auto root = MyServer::Payloads::CreateRoot(
                builder,
                MyServer::Payloads::AnyPayload_ReverseRequest, // Set the union type
                reverse_payload.Union() // Get the offset to the payload
            );

            builder.Finish(root, FILE_IDENTIFIER);
            send_request(builder);
        }

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}

/**
 * @brief Connects to the server, sends the buffer, and prints the response.
 * @param builder The FlatBufferBuilder containing the finished buffer.
 */
void send_request(flatbuffers::FlatBufferBuilder& builder) {
    // Get pointer and size from the builder
    uint8_t* buf = builder.GetBufferPointer();
    int payload_len = builder.GetSize();

    // Create the full message: identifier + length + payload
    std::vector<uint8_t> message;
    message.reserve(8 + payload_len);

    // 1. Add file identifier (4 bytes)
    message.insert(message.end(), FILE_IDENTIFIER, FILE_IDENTIFIER + 4);

    // 2. Add payload length (4 bytes, little-endian)
    // This assumes the host machine is little-endian (like x86)
    message.insert(message.end(), reinterpret_cast<uint8_t*>(&payload_len), reinterpret_cast<uint8_t*>(&payload_len) + 4);

    // 3. Add the FlatBuffer payload
    message.insert(message.end(), buf, buf + payload_len);

    // --- Socket Communication ---
    int sock = 0;
    sockaddr_un serv_addr{};

    if ((sock = socket(AF_UNIX, SOCK_STREAM, 0)) < 0) {
        throw std::runtime_error("Socket creation error");
    }

    memset(&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sun_family = AF_UNIX;
    strncpy(serv_addr.sun_path, SOCKET_PATH, sizeof(serv_addr.sun_path) - 1);

    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        throw std::runtime_error("Connection Failed");
    }

    std::cout << "\n--- Sending request ---" << std::endl;
    std::cout << "Client: Sending " << message.size() << " bytes total." << std::endl;

    // Send the message
    send(sock, message.data(), message.size(), 0);

    // Receive the response
    char buffer[1024] = {0};
    int valread = read(sock, buffer, 1024);
    if (valread > 0) {
        std::cout << "Client: Received response -> " << std::string(buffer, valread) << std::endl;
    }

    // Close the socket
    close(sock);
}
