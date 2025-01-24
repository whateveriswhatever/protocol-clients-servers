const net = require("net");
const fs = require("fs");

const client = new net.Socket();

client.connect(8080, "localhost", () => {
  console.log("Connected to server");

  // Test with CSV file
  const csvData = `SysCode,SysName,DeviceCode,DeviceName,DataExtType,Content,Remark
UVWX,GHI,1234,JK,5,mnop,qrsuvwxy
ABCD,JKL,5678,LM,7,qrst,xyzabcde
EFGH,MNO,9101,NO,9,uvwx,defghijk
IJKL,PQR,2345,QR,11,xyza,ghijklmn`;

  //   console.log("Sending CSV data...");
  //   client.write(csvData);

  // Test with JSON file
  const jsonData = JSON.stringify([
    {
      system_code: "938276",
      system_name: "abcde",
      device_code: "laptop",
      device_name: "laptop3",
      alert_type: 15,
      description: "CPU overheat",
      note: "Check cooling system",
    },
    {
      system_code: "847362",
      system_name: "lmnop",
      device_code: "tablet",
      device_name: "tablet9",
      alert_type: 30,
      description: "Battery low",
      note: "Recharge immediately",
    },
    {
      system_code: "726493",
      system_name: "qrstu",
      device_code: "smartphone",
      device_name: "smartphone2",
      alert_type: 8,
      description: "Software update required",
      note: "Install latest update",
    },
    {
      system_code: "514839",
      system_name: "vwxyz",
      device_code: "desktop",
      device_name: "desktop5",
      alert_type: 22,
      description: "Network error detected",
      note: "Check network connections",
    },
  ]);

  // Send CSV data
  //   client.write(csvData);
  client.write(jsonData);
  // Send JSON data after a delay
  //   setTimeout(() => {
  //     client.write(jsonData);
  //   }, 1000);
});

client.on("data", (data) => {
  console.log("Received:", data.toString());
});

client.on("error", (err) => {
  console.error("Error:", err.message);
});

client.on("close", () => {
  console.log("Connection closed");
});
