const net = require("net");

// Track all connected Socket clients
const connectedSockets = new Set();

const CURRENT_USER = "whateveriswhatever";
const CURRENT_UTC = "2025-01-24 03:35:27";

let isProcessing = false;

const readFramedMessage = (data) => {
  // First 4 bytes are the length prefix
  const messageLength = data.readUInt32BE(0);

  // Extracting the actual message data, starting after the length prefix
  const messageData = data.slice(4, 4 + messageLength);
  return messageData.toString("utf8");
};

// Helper function to create framed message
const createFramedMessage = (message) => {
  const messageBuffer = Buffer.from(message);
  const lengthBuffer = Buffer.alloc(4);
  lengthBuffer.writeUInt32BE(messageBuffer.length);
  return Buffer.concat([lengthBuffer, messageBuffer]);
};

const server = net.createServer((socket) => {
  console.log(`[${CURRENT_UTC}] New client connected by ${CURRENT_USER}!`);

  // Creating a buffer for this connection
  let messageBuffer = Buffer.alloc(0);

  connectedSockets.add(socket);

  socket.on("data", async (data) => {
    if (isProcessing) {
      console.log(`[${CURRENT_UTC}] Already processing data, skipping...`);
      return;
    }

    try {
      isProcessing = true;

      // Combining with any previously buffered data
      messageBuffer = Buffer.concat([messageBuffer, data]);

      // Process all complete messages in the buffer
      while (messageBuffer.length >= 4) {
        const messageLength = messageBuffer.readUInt32BE(0);
        const totalLength = messageLength + 4;

        if (messageBuffer.length < totalLength) {
          // Not enough data for a complete message
          break;
        }

        // Extract the complete message
        const stringData = readFramedMessage(messageBuffer);

        // Update buffer to remove processed message
        messageBuffer = messageBuffer.subarray(totalLength);

        // Add debug logging
        console.log(`[${CURRENT_UTC}] Received data length: ${messageLength}`);
        console.log(
          `[${CURRENT_UTC}] First 200 characters of received data: ${stringData.substring(
            0,
            200
          )}`
        );

        // Try to parse as JSON first
        try {
          const parsed = JSON.parse(stringData);
          if (Array.isArray(parsed)) {
            console.log(`[${CURRENT_UTC}] Successfully parsed as JSON array`);
            await handleJSONData(stringData, socket);
            continue;
          } else {
            console.log(`[${CURRENT_UTC}] Parsed as JSON but not an array`);
          }
        } catch (e) {
          console.log(`[${CURRENT_UTC}] JSON parse error: ${e.message}`);
        }

        // Try CSV if JSON fails
        if (isCSV(stringData)) {
          console.log(`[${CURRENT_UTC}] Received CSV data`);
          await handleCSVData(stringData, socket);
        } else {
          throw new Error(
            "Invalid data format. Expected either JSON array or CSV data."
          );
        }
      }
    } catch (error) {
      console.error(`[${CURRENT_UTC}] Error processing data:`, error.message);
      const errorMsg = JSON.stringify({
        error: error.message,
        timestamp: CURRENT_UTC,
        user: CURRENT_USER,
      });
      socket.write(createFramedMessage(errorMsg));
    } finally {
      isProcessing = false;
    }
  });

  socket.on("error", (err) => {
    console.error(`[${CURRENT_UTC}] Socket error: ${err.message}`);
    connectedSockets.delete(socket);
    isProcessing = false;
  });

  socket.on("close", () => {
    console.log(`[${CURRENT_UTC}] Client disconnected!`);
    connectedSockets.delete(socket);
    isProcessing = false;
  });
});

const isCSV = (data) => {
  const lines = data.split("\n").filter((line) => line.trim().length > 0);
  if (lines.length < 2) return false;

  const firstLineColumns = lines[0].split(",").length;
  return lines.every((line) => {
    const columns = line.split(",").length;
    return columns === firstLineColumns && columns > 1;
  });
};

const handleCSVData = async (data, sender) => {
  const rows = data.split("\n").filter((row) => row.trim());

  if (rows.length < 2) {
    throw new Error("CSV must contain a header row and at least one data row");
  }

  const headerRow = rows[0];
  const dataRows = rows.slice(1);

  console.log(`[${CURRENT_UTC}] CSV Header: ${headerRow}`);
  console.log(`[${CURRENT_UTC}] Processing ${dataRows.length} data rows`);

  for (let i = 0; i < dataRows.length; i++) {
    const row = dataRows[i].trim();
    if (row) {
      console.log(
        `[${CURRENT_UTC}] Broadcasting row ${i + 1}/${dataRows.length}: ${row}`
      );

      await broadcastToClients(row, sender);

      if (i < dataRows.length - 1) {
        await new Promise((resolve) => setTimeout(resolve, 500));
      }
    }
  }

  console.log(`[${CURRENT_UTC}] Finished broadcasting all rows`);
};

const isJSON = (data) => {
  try {
    const parsed = JSON.parse(data);
    return Array.isArray(parsed);
  } catch (e) {
    return false;
  }
};

const handleJSONData = async (data, sender) => {
  const jsonData = JSON.parse(data);

  if (!Array.isArray(jsonData)) {
    throw new Error("JSON data must be an array of objects");
  }

  console.log(`[${CURRENT_UTC}] Processing ${jsonData.length} JSON objects`);

  for (let i = 0; i < jsonData.length; i++) {
    const object = jsonData[i];
    if (typeof object !== "object" || object === null) {
      throw new Error(`Invalid object at index ${i}`);
    }

    console.log(
      `[${CURRENT_UTC}] Broadcasting object ${i + 1}/${jsonData.length}`
    );
    await broadcastToClients(JSON.stringify(object), sender);

    if (i < jsonData.length - 1) {
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
  }

  console.log(`[${CURRENT_UTC}] Finished broadcasting all JSON objects`);
};

const broadcastToClients = (message, sender) => {
  return new Promise((resolve, reject) => {
    const clients = Array.from(connectedSockets).filter(
      (socket) => socket !== sender
    );
    if (clients.length === 0) {
      resolve();
      return;
    }

    let completed = 0;
    let hasError = false;

    const framedMessage = createFramedMessage(message);

    clients.forEach((socket) => {
      if (!socket.destroyed) {
        socket.write(framedMessage, (err) => {
          if (err && !hasError) {
            hasError = true;
            connectedSockets.delete(socket);
            reject(err);
            return;
          }

          completed++;
          if (completed === clients.length && !hasError) {
            resolve();
          }
        });
      } else {
        completed++;
        connectedSockets.delete(socket);
        if (completed === clients.length && !hasError) {
          resolve();
        }
      }
    });
  });
};

const PORT = 8080;

server.listen(PORT, () => {
  console.log(`[${CURRENT_UTC}] Socket TCP server running on port ${PORT}`);
  console.log(`[${CURRENT_UTC}] Server started by ${CURRENT_USER}`);
});
