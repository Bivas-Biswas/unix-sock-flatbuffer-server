const net = require('net');
const flatbuffers = require('flatbuffers');

// --- 1. Import Generated FlatBuffers Code ---
// The generated JS file must be converted to a CommonJS module for Node.js.
// To do this, you MUST add the following line to the VERY BOTTOM of schema_generated.js.
//
// module.exports = MyServer;
//
// IMPORTANT: The 'MyServer' variable name is based on the first namespace in your
// schema.fbs file ('namespace MyServer.Payloads;'). If you change the namespace,
// you must change the variable name here and in the module.exports line.
// DO NOT add or change anything else in the generated file.
const { MyServer } = require('./schema_generated.js');

// --- Defensive Check ---
// This check helps diagnose if the module was loaded correctly.
if (!MyServer || !MyServer.Payloads || !MyServer.Payloads.EchoRequest || !MyServer.Payloads.ReverseRequest) {
    console.error("Fatal Error: Failed to load FlatBuffers modules from schema_generated.js.");
    console.error("Please ensure you have added 'module.exports = MyServer;' to the end of that file.");
    process.exit(1);
}


// --- Configuration ---
const FILE_IDENTIFIER = "PLDE"; // Must match your server
const SOCKET_PATH = "/tmp/my_server.sock";

/**
 * Creates a FlatBuffer payload for an ECHO request.
 * @param {flatbuffers.Builder} builder
 * @param {string} message
 * @returns {number} The offset of the created payload.
 */
function createEchoPayload(builder, message) {
    const msg_str = builder.createString(message);
    MyServer.Payloads.EchoRequest.startEchoRequest(builder);
    MyServer.Payloads.EchoRequest.addMessage(builder, msg_str);
    return MyServer.Payloads.EchoRequest.endEchoRequest(builder);
}

/**
 * Creates a FlatBuffer payload for a REVERSE request.
 * @param {flatbuffers.Builder} builder
 * @param {string} data
 * @returns {number} The offset of the created payload.
 */
function createReversePayload(builder, data) {
    const data_str = builder.createString(data);
    MyServer.Payloads.ReverseRequest.startReverseRequest(builder);
    MyServer.Payloads.ReverseRequest.addData(builder, data_str);
    return MyServer.Payloads.ReverseRequest.endReverseRequest(builder);
}

/**
 * Builds the final FlatBuffer, sends it via TCP, and waits for a response.
 * @param {flatbuffers.Builder} builder
 * @param {number} payloadType
 * @param {number} payloadOffset
 */
function sendRequest(builder, payloadType, payloadOffset) {
    MyServer.Payloads.Root.startRoot(builder);
    MyServer.Payloads.Root.addPayloadType(builder, payloadType);
    MyServer.Payloads.Root.addPayload(builder, payloadOffset);
    const root = MyServer.Payloads.Root.endRoot(builder);

    builder.finish(root, FILE_IDENTIFIER);

    const buf = builder.asUint8Array(); // Get the Uint8Array
    const payload_len = buf.length;

    // Create the full message: identifier (4 bytes) + length (4 bytes) + payload
    const header = Buffer.alloc(8);
    header.write(FILE_IDENTIFIER, 0, 4, 'ascii');
    header.writeUInt32LE(payload_len, 4);

    const fullMessage = Buffer.concat([header, buf]);

    // --- TCP Socket Communication ---
    const client = new net.Socket();
    client.connect(SOCKET_PATH, () => {
        console.log(`\n--- Sending request of type ${payloadType} ---`);
        console.log(`Client: Connected to TCP server.`);
        console.log(`Client: Sending ${fullMessage.length} bytes total.`);
        client.write(fullMessage);
    });

    client.on('data', (data) => {
        console.log(`Client: Received response -> ${data.toString()}`);
        client.destroy(); // Close the connection after receiving data
    });

    client.on('close', () => {
        console.log('Client: Connection closed.');
    });

    client.on('error', (err) => {
        console.error(`Client: Connection error: ${err.message}`);
    });
}


// --- Main Execution ---
function main() {
    // Example 1: Send an ECHO request
    const builderEcho = new flatbuffers.Builder(1024);
    const echoOffset = createEchoPayload(builderEcho, "Hello from Node.js!");
    sendRequest(builderEcho, MyServer.Payloads.AnyPayload.EchoRequest, echoOffset);

    // Example 2: Send a REVERSE request (after a delay)
    setTimeout(() => {
        const builderReverse = new flatbuffers.Builder(1024);
        const reverseOffset = createReversePayload(builderReverse, "Node.js reverse test");
        sendRequest(builderReverse, MyServer.Payloads.AnyPayload.ReverseRequest, reverseOffset);
    }, 1000); // 1-second delay
}

main();
