// const net = require("net");
// const fs = require("fs");

// // Track all connected Socket clients
// const connectedSockets = new Set();

// const CURRENT_USER = "whateveriswhatever";
// const CURRENT_UTC = "2025-01-24 03:14:29";

// // Define message delimeter
// const MESSAGE_DELIMITER = "||END_OF_MESSAGE||";

// // Add processing lock
// let isProcessing = false;

// const server = net.createServer((socket) => {
//   console.log(`[${CURRENT_UTC}] New client connected by ${CURRENT_USER}!`);

//   connectedSockets.add(socket);

//   socket.on("data", async (data) => {
//     // Check if we're already processing data
//     if (isProcessing) {
//       console.log(`[${CURRENT_UTC}] Already processing data, skipping...`);
//       return;
//     }

//     try {
//       isProcessing = true;
//       const stringData = data.toString();

//       if (isCSV(stringData)) {
//         console.log(`[${CURRENT_UTC}] Received CSV data`);
//         await handleCSVData(stringData, socket);
//       } else if (isJSON(stringData)) {
//         console.log(`[${CURRENT_UTC}] Received JSON data`);
//         await handleJSONData(stringData, socket);
//       } else {
//         throw new Error(
//           "Invalid data format. Expected either JSON array or CSV data."
//         );
//       }
//     } catch (error) {
//       console.error(`[${CURRENT_UTC}] Error processing data:`, error.message);
//       socket.write(
//         JSON.stringify({
//           error: error.message,
//           timestamp: CURRENT_UTC,
//           user: CURRENT_USER,
//         }) + MESSAGE_DELIMITER
//       );
//     } finally {
//       isProcessing = false;
//     }
//   });

//   socket.on("error", (err) => {
//     console.error(`[${CURRENT_UTC}] Socket error: ${err.message}`);
//     connectedSockets.delete(socket);
//     isProcessing = false;
//   });

//   socket.on("close", () => {
//     console.log(`[${CURRENT_UTC}] Client disconnected!`);
//     connectedSockets.delete(socket);
//     isProcessing = false;
//   });
// });

// const isCSV = (data) => {
//   const lines = data.split("\n").filter((line) => line.trim().length > 0);
//   if (lines.length < 2) return false;

//   const firstLineColumns = lines[0].split(",").length;
//   return lines.every((line) => {
//     const columns = line.split(",").length;
//     return columns === firstLineColumns && columns > 1;
//   });
// };

// const isJSON = (data) => {
//   try {
//     const parsed = JSON.parse(data);
//     return Array.isArray(parsed);
//   } catch (e) {
//     return false;
//   }
// };

// const handleCSVData = async (data, sender) => {
//   const rows = data.split("\n").filter((row) => row.trim());

//   if (rows.length < 2) {
//     throw new Error("CSV must contain a header row and at least one data row");
//   }

//   const headerRow = rows[0];
//   const dataRows = rows.slice(1);

//   console.log(`[${CURRENT_UTC}] CSV Header: ${headerRow}`);
//   console.log(`[${CURRENT_UTC}] Processing ${dataRows.length} data rows`);

//   for (let i = 0; i < dataRows.length; i++) {
//     const row = dataRows[i].trim();
//     if (row) {
//       console.log(
//         `[${CURRENT_UTC}] Broadcasting row ${i + 1}/${dataRows.length}: ${row}`
//       );

//       await broadcastToClients(row + MESSAGE_DELIMITER, sender);

//       // Add delay between messages
//       if (i < dataRows.length - 1) {
//         await new Promise((resolve) => setTimeout(resolve, 500));
//       }
//     }
//   }

//   console.log(`[${CURRENT_UTC}] Finished broadcasting all rows`);
// };

// const handleJSONData = async (data, sender) => {
//   const jsonData = JSON.parse(data);

//   if (!Array.isArray(jsonData)) {
//     throw new Error("JSON data must be an array of objects");
//   }

//   console.log(`[${CURRENT_UTC}] Processing ${jsonData.length} JSON objects`);

//   for (let i = 0; i < jsonData.length; i++) {
//     const object = jsonData[i];
//     if (typeof object !== "object" || object === null) {
//       throw new Error(`Invalid object at index ${i}`);
//     }

//     console.log(
//       `[${CURRENT_UTC}] Broadcasting object ${i + 1}/${jsonData.length}`
//     );

//     await broadcastToClients(JSON.stringify(object) + "\n", sender);

//     // Add delay between objects except for the last one
//     if (i < jsonData.length - 1) {
//       await new Promise((resolve) => setTimeout(resolve, 500));
//     }
//   }

//   console.log(`[${CURRENT_UTC}] Finished broadcasting all JSON objects`);
// };

// const broadcastToClients = (message, sender) => {
//   return new Promise((resolve, reject) => {
//     const clients = Array.from(connectedSockets).filter(
//       (socket) => socket !== sender
//     );
//     if (clients.length === 0) {
//       resolve();
//       return;
//     }

//     let completed = 0;
//     let hasError = false;

//     clients.forEach((socket) => {
//       if (!socket.destroyed) {
//         socket.write(message, (err) => {
//           if (err && !hasError) {
//             hasError = true;
//             connectedSockets.delete(socket);
//             reject(err);
//             return;
//           }

//           completed++;
//           if (completed === clients.length && !hasError) {
//             resolve();
//           }
//         });
//       } else {
//         completed++;
//         connectedSockets.delete(socket);
//         if (completed === clients.length && !hasError) {
//           resolve();
//         }
//       }
//     });
//   });
// };

// const PORT = 8080;

// server.listen(PORT, () => {
//   console.log(`[${CURRENT_UTC}] Socket TCP server running on port ${PORT}`);
//   console.log(`[${CURRENT_UTC}] Server started by ${CURRENT_USER}`);
// });

const net = require("net");

// Track all connected Socket clients
const connectedSockets = new Set();

const CURRENT_USER = "whateveriswhatever";
const CURRENT_UTC = "2025-01-24 03:35:27";

let isProcessing = false;

// Helper function to create framed message
const createFramedMessage = (message) => {
  const messageBuffer = Buffer.from(message);
  const lengthBuffer = Buffer.alloc(4);
  lengthBuffer.writeUInt32BE(messageBuffer.length);
  return Buffer.concat([lengthBuffer, messageBuffer]);
};

const server = net.createServer((socket) => {
  console.log(`[${CURRENT_UTC}] New client connected by ${CURRENT_USER}!`);

  connectedSockets.add(socket);

  socket.on("data", async (data) => {
    if (isProcessing) {
      console.log(`[${CURRENT_UTC}] Already processing data, skipping...`);
      return;
    }

    try {
      isProcessing = true;
      const stringData = data.toString();

      if (isCSV(stringData)) {
        console.log(`[${CURRENT_UTC}] Received CSV data`);
        await handleCSVData(stringData, socket);
      } else if (isJSON(stringData)) {
        console.log(`[${CURRENT_UTC}] Received JSON data`);
        await handleJSONData(stringData, socket);
      } else {
        throw new Error(
          "Invalid data format. Expected either JSON array or CSV data."
        );
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
