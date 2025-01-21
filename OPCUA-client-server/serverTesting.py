import asyncio
import logging
from asyncua import ua, Server, uamethod
import json
from datetime import datetime
import csv
from io import StringIO

class UAServer:
    def __init__(self, endpoint, username, password):
        self._endpoint = endpoint
        self._username = username
        self._password = password
        self._server = None
        self._running = False
        
        # Configured logging
        logging.basicConfig(level=logging.INFO)
        self._logger = logging.getLogger("asyncua.server")
        
        # Store client subscriptions
        self._subscriptions = set()
        
    async def init_server(self):
        """Initialize the OPC UA server with security settings"""
        self._server = Server()
        
        # Server setup
        await self._server.init()
        
        # Set server endpoint
        self._server.set_endpoint(self._endpoint)
        
        # Set server name
        self._server.set_server_name("UA Test Server")
        
        # Set server security
        await self.setup_security()
        
        # Setup namespace
        self._URI = "https://examples.open&free.com/ua/"
        self._IDX = await self._server.register_namespace(self._URI)
        
        # Create base structure
        await self.create_server_structure()
        
        return True
    
    async def setup_data_change_notifications(self):
        """Set up server-side monitoring of data changes"""
        if hasattr(self, "_ext_system_data"):
            await self._ext_system_data.set_writable()
            await self._ext_system_data.set_value_rank(ua.ValueRank.Scalar)
            await self._ext_system_data.set_data_type(ua.NodeId(ua.ObjectIds.String))
            
            # Setting up monitoring parameters
            params = ua.DataChangeFilter()
            params.trigger = ua.DataChangeTrigger.StatusValue
            params.deadbandtype = ua.DeadbandType.None_
            params.deadbandvalue = 0.0
            
            # Creating monitored item
            await self._server.create_monitored_items([self._ext_system_data], params)
    
    async def create_server_structure(self):
        """Create the server's node structure"""
        try:
            # Get root node
            objects = self._server.nodes.objects
            
            # Create main folder
            self._logger.info("Creating Channel1 folder...")
            channel1 = await objects.add_folder(self._IDX, "Channel1")
            
            # Create H07 sub-folder
            self._logger.info("Creating H07 sub-folder...")
            h07 = await channel1.add_folder(self._IDX, "H07")
            
            # Create the variable with an initial null state
            # This won't trigger unnecessary notifications
            self._ext_system_data = await h07.add_variable(
                nodeid=ua.NodeId("Channel.H07.ExtSystemData", self._IDX),
                bname="ExtSystemData",
                val=""  # Initialize with empty string to avoid triggering notifications
            )
        
            # Set variable to be writable
            await self._ext_system_data.set_writable()    
            
            self._logger.info(f"Created ExtSystemData node with ID : {self._ext_system_data.nodeid}")
            
            # Set up value write handler
            await self._ext_system_data.set_writable(True)
            self._server.subscribe_server_callback(ua.AttributeIds.Value, self.on_value_change)
            
        except Exception as ex:
            self._logger.error(f"Error in creating the server structure ----> {str(ex)}")
            raise
    
    def parse_csv_to_json(self, csv_string):
        """Convert CSV string into JSON format"""
        try:
            # Use StringIO to erect a file-like object from the string
            csv_file = StringIO(csv_string)
            csv_reader = csv.DictReader(csv_file)
            
            # Convert CSV rows to list of dictionaries
            data = list(csv_reader)
            
            if not data:
                raise ValueError("Empty CSV data")

            return json.dumps(data)
        except Exception as ex:
            self._logger.error(f"CSV parsing error ----> {str(ex)}")
            raise
    
    def parse_json_to_csv(self, json_string):
        """Convert JSON string to CSV format"""
        try:
            # Parse JSON string to Python object
            data = json.loads(json_string)
            
            if not data or not isinstance(data, list):
                raise ValueError("Invalid JSON data structure!!!")
            
            # Get headers from the first dictionary
            headers = data[0].keys()
            
            # Create StringIO object to write CSV
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=headers)
            
            # Write headers and rows
            writer.writeheader()
            writer.writerows(data)
            
            return output.getvalue()
        
        except Exception as ex:
            self._logger.error(f"JSON to CSV format conversion error ----> {str(ex)}")
            raise
            
    async def on_value_change(self, node, val):
        """Handler for value changes from clients"""
        try:
            if node == self._ext_system_data.nodeid:
                self._logger.info(f"Received value change from client: {val}")
                
                # Detect if the incoming data is CSV or JSON
                try:
                    # Try to parse as JSON object
                    json.loads(val)
                    processed_val = val
                except json.JSONDecodeError:
                    # If JSON parsing is failed, assuming that the data format is CSV and converting it into JSON
                    self._logger.info("Converting CSV to JSON format...")
                    processed_val = self.parse_csv_to_json(val)
                
                # Create a proper DataValue object for relay
                dv = ua.DataValue(
                    ua.Variant(processed_val, ua.VariantType.String)
                )
                dv.ServerTimestamp = datetime.now()
                dv.SourceTimestamp = datetime.now()
                
                # Relay the message to all subscribed clients
                await self._ext_system_data.write_value(dv, force=True) # using `force` to force the server broadcasting the message even though the node's value ain't change
                
        except Exception as ex:
            self._logger.error(f"Error handling value change: {str(ex)}")
    
    async def setup_security(self):
        """Setup server security settings"""
        # Set up security policies
        self._server.set_security_policy(
            [
                ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
                ua.SecurityPolicyType.Basic256Sha256_Sign,
                ua.SecurityPolicyType.NoSecurity
            ]
        )
        
        # Setup user authentication
        user_manager = UserManager()
        user_manager.add_user(self._username, self._password)
        self._server.user_manager = user_manager
    
    async def start(self):
        """Start the OPC UA server"""
        self._running = True

        try:
            self._logger.info("Starting server initialization...")
            await self.init_server()

            self._logger.info("Starting server...")
            async with self._server:
                self._logger.info(f"Server started at {self._endpoint}")

                # Keep the server running
                while self._running:
                    await asyncio.sleep(1)

        except Exception as ex:
            self._logger.error(f"Server error ----> {str(ex)}")
            if self._server:
                await self._server.stop()
            raise
    
    async def stop(self):
        """Stop the OPC UA server"""
        self._running = False
        if self._server is not None:
            try:
                await self._server.stop()
                self._logger.info("Server stopped successfully!!!")
            except Exception as ex:
                self._logger.error(f"Error in stopping the server ----> {str(ex)}")

class UserManager:
    """User manager for handling authentication"""
    
    def __init__(self):
        self._users = {}
        
    def add_user(self, username, password):
        """Add a new user"""
        self._users[username] = password
    
    def validate_user(self, isession, username, password):
        """Validate user credentials"""
        if username in self._users and self._users[username] == password:
            return True
        
        return False


async def main():
    host = "127.0.0.1" # or "0.0.0.0" to allow external connections
    port = 4840
    server_endpoint = f"opc.tcp://{host}:{port}"
    username = "admin"
    password = "loz1234"
    
    server = UAServer(server_endpoint, username, password)
    
    try:
        # Run the server
        await server.start()
        
    except KeyboardInterrupt:
        # Handle graceful shutdown
        await server.stop()
    
    except Exception as ex:
        logging.error("Main error ----> {}".format(str(ex)))
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())