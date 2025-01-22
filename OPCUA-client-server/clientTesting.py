import asyncio
import logging
from asyncua import Client, ua, Node
import json
from datetime import datetime

class UAClient:
    def __init__(self, endpoint, username, password):
        self._endpoint = endpoint
        self._username = username
        self._password = password
        self._client = None
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self._logger = logging.getLogger("asyncua.client")
        
    async def connect(self):
        """Connect to the OPC UA server"""
        try:
            self._client = Client(url=self._endpoint)
            
            # Use username/password authentication without encryption
            # This matches the server's available security policy
            self._client.set_user(self._username)
            self._client.set_password(self._password)
            
            # Connect to server
            await self._client.connect()
            self._logger.info("Connected to OPC UA server")
            
            # Get the node we want to interact with
            uri = "https://examples.open&free.com/ua/"
            idx = await self._client.get_namespace_index(uri)
            
            # Get the ExtSystemData node using the correct node ID format
            node_id = ua.NodeId("Channel.H07.ExtSystemData", idx)
            self._ext_system_data = self._client.get_node(node_id)
            
            return True
            
        except Exception as ex:
            self._logger.error(f"Connection error: {str(ex)}")
            raise
            
    async def send_message(self, message_data, format_type="json"):
        """Send a message to the server"""
        
        """
        Args:
            message data : Either a dictionary (for JSON) or CSV string
            format type : JSON or CSV
        
        """
        
        
        try:
            if format_type.lower() == "json":
                if not isinstance(message_data, dict):
                    raise ValueError("JSON message data must be a dictionary!!!")
                message_str = json.dumps(message_data)
            
            elif format_type.lower() == "csv":
                if not isinstance(message_data, str):
                    raise ValueError("CSV message data must be a string!!!")
                message_str = message_data
            
            else:
                raise ValueError("Invalid format type!!! Using 'json' or 'csv'!")
        
            
            # Create proper DataValue object
            dv = ua.DataValue(
                ua.Variant(message_str, ua.VariantType.String)
            )
            
            # Write the value to the node
            await self._ext_system_data.write_value(dv)
            
            self._logger.info(f"Message sent successfully: {message_data}")
            
        except Exception as ex:
            self._logger.error(f"Error sending message: {str(ex)}")
            raise
            
    async def subscribe_to_messages(self, callback):
        """Subscribe to messages from the server"""
        try:
            # Create subscription
            subscription = await self._client.create_subscription(
                period=500,  # Publishing interval in ms
                handler=MessageHandler(callback)
            )
            
            # Create monitored item for the node
            await subscription.subscribe_data_change(self._ext_system_data)
            
            self._logger.info("Subscribed to messages successfully")
            
            return subscription
            
        except Exception as ex:
            self._logger.error(f"Subscription error: {str(ex)}")
            raise
            
    async def disconnect(self):
        """Disconnect from the OPC UA server"""
        if self._client:
            try:
                await self._client.disconnect()
                self._logger.info("Disconnected from server")
            except Exception as ex:
                self._logger.error(f"Disconnection error: {str(ex)}")

class MessageHandler:
    """Handler for data change notifications"""
    def __init__(self, callback):
        self._callback = callback
        self._logger = logging.getLogger("asyncua.client.handler")
        
    async def datachange_notification(self, node, val, data):
        """Called when the server sends a data change notification"""
        try:
            # Parse the JSON string
            message_data = json.loads(val)
            
            # Call the callback function with the message
            await self._callback(message_data)
            
        except Exception as ex:
            self._logger.error(f"Error handling notification: {str(ex)}")

async def message_callback(message):
    """Example callback function for received messages"""
    print(f"Received message: {message}")

async def main():
    # Connection details matching the server
    host = "127.0.0.1"
    port = 4840
    endpoint = f"opc.tcp://{host}:{port}"
    username = "admin"
    password = "loz1234"
    
    client = UAClient(endpoint, username, password)
    
    try:
        # Connect to server
        await client.connect()
        
        # Subscribe to messages
        subscription = await client.subscribe_to_messages(message_callback)
        
        # Example: Send a test message
        test_message = {
            "system_code": "CLIENT002",
            "system_name": "Client B",
            "device_code": "Device Z",
            "device_name": "poipopzzz",
            "alert_type": 3,
            "alert_content": "Client 2 test message",
            "note": "Sent from client 2"
        }
        
        test_csv_message = """CLIENT008,Client FVG,Device X,...,2,Client 2 test message,Sent from client 2"""
        
        await client.send_message(test_csv_message, format_type="csv")
        
        # Keep the client running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
            
    finally:
        # Clean up
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())