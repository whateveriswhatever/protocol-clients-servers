const net = require("net");
const fs = require("fs");

// Track all connected Socket clients
const connectedSockets = new Set();

const server = net.createServer((socket) => {
  console.log("New client connected!");

  connectedSockets.add(socket);

  socket.on("data", (data) => {
    const stringData = data.toString().trim();

    try {
      // Try to parse JSON data
      try {
        const message = JSON.parse(stringData);
        console.log(`Received JSON data: ${JSON.stringify(message, null, 2)}`);
        broadcastMessage(JSON.stringify(message), socket);
        return;
      } catch (jsonError) {
        // If data is not JSON, check for CSV format
        if (isCSV(stringData)) {
          console.log(`Received CSV data:\n${stringData}`);
          broadcastMessage(stringData, socket);
          return;
        }
        throw new Error("Unrecognized data format.");
      }
    } catch (error) {
      console.error(`Error processing message: ${error.message}`);
      socket.write(
        JSON.stringify({
          error: "Invalid data format. Expected JSON or CSV.",
          details: error.message,
        })
      );
    }
  });

  socket.on("error", (err) => {
    console.error(`Socket error: ${err.message}`);
  });

  socket.on("close", () => {
    console.log("Client disconnected!");
    connectedSockets.delete(socket);
  });
});

// Broadcast message to all clients except the sender
const broadcastMessage = (message, sender) => {
  for (const socket of connectedSockets) {
    if (socket !== sender && !socket.destroyed) {
      try {
        socket.write(message);
        console.log("Message broadcasted successfully!");
      } catch (err) {
        console.error(`Error broadcasting to a client: ${err.message}`);
        connectedSockets.delete(socket);
      }
    }
  }
};

// Validate if data is in CSV format
const isCSV = (data) => {
  const lines = data.split("\n");
  return (
    lines.length > 0 &&
    lines[0].includes(",") &&
    lines.every((line) => line.split(",").length > 1)
  );
};

const PORT = 8080;

server.listen(PORT, () => {
  console.log(`Socket TCP server running on port ${PORT}`);
});
