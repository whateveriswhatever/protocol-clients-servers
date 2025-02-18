from opcua import Client
import time
import json
import csv

class OPCUA_Client:
    def __init__(self, serverURL,username, password, nodeID):
        self._client = Client(serverURL)
        self._username = username
        self._password = password
        self._serverURL = serverURL
        self._nodeID = nodeID
        self._node = None
    
    def connect_to_server(self):
        try:
            self._client.set_user(self._username)
            self._client.set_password(self._password)
            self._client.connect()
            print("Connected to {} as {}".format(self._serverURL, self._username))
            self._node = self._client.get_node(self._nodeID)
        except Exception as ex:
            print(f"Failed to connect {ex}")
    
    def read_value_from_node(self, node_id):
        try:
            node = self._client.get_node(node_id)
            return node.get_value()
        except Exception as ex:
            print(f"Error in reading node value: {ex}")
            return None
    
    def disconnect_from_server(self):
        self._client.disconnect()
        print("Disconnected from server")
    
    def read_node_value_continuosly_mode(self):
        while True:
            data_value = opcua_client.read_value_from_node(self._node)
            if data_value is not None:
                print("Current node's value: {}".format(data_value))
            time.sleep(1)
    
    def write_plain_text(self):
        # node = self._client.get_node("ns=2;i=2")
        txt = str(input("Enter a plain text: "))
        self._node.set_value(txt)
        
    def write_json_text(self):
        
        json_txt = str(input("Enter a JSON object: "))
        try:
            json_obj = json.loads(json_txt)
            json_value = json.dumps(json_obj) # Converting the JSON object into string format
            self._node.set_value(json_value)
        except:
            pass    
    
    def write_value_mode(self):
        print("\n1. Sending an custom raw message")
        print("2. Sending an custom JSON object")
        user_selected_option = int(input("Your option: "))
        
        cases = {
            1: self.write_plain_text,
            2: self.write_json_text
            
        }
        
        def switch_case(case):
            return cases.get(case)()
        
        result = switch_case(user_selected_option)
        print(result)
        
    def send_json(self, json_obj):
        json_str = json.dumps(json_obj)
        
        self._node.set_value(json_str)
        
    def send_plain_text(self, text):
        
        self._node.set_value(text)
    
    def send_json_file(self, file_path):
        with open(file_path, 'r') as json_file:
            try:
                data = json.load(json_file)
                print(data)
                storage = list(data)
                for json_obj in storage:
                    self.send_json(json_obj)
                    time.sleep(1)
            finally:
                json_file.close()
        
        
    
    def send_csv_file(self, file_path):
        """Sending the entire CSV content except for the header row"""
        # Each CSV data row will be sent in plain-text format
        with open(file_path, 'r') as csv_file:
            try:
                csv_reader = csv.reader(csv_file)
                print(csv_reader)
                
                # Skipping the header row
                next(csv_reader)
                
                for row in csv_reader:
                    print(row)
                    if len(row) != 0:
                        data_row_str = ','.join(row)
                        self.send_plain_text(data_row_str)
                    
                    time.sleep(1.5)
            finally:
                csv_file.close()
            

url = "opc.tcp://172.26.50.95:4840"
username = "admin"
password = "loz1234"

nodeID = input("Enter node ID: ")

opcua_client = OPCUA_Client(url, username, password, nodeID)
opcua_client.connect_to_server()



try:
    while True:
        print("Client interface: ")
        print("****")
        print("\t Option 1: Reading data from server continously")
        print("\t Option 2: Writing data on node")
        print("\t Option 3: Sending JSON file to node")
        print("\t Option 4: Sending CSV file to node")
        
        selected_mode = int(input("Enter your option: "))
        
        if selected_mode == 1:
            opcua_client.read_node_value_continuosly_mode()
        
        if selected_mode == 2:
            opcua_client.write_value_mode()
        
        if selected_mode == 3:
            filePath = str(input("Enter the JSON file path: "))
            opcua_client.send_json_file(filePath)
        
        if selected_mode == 4:
            filePath = str(input("Enter the CSV file path: "))
            opcua_client.send_csv_file(filePath)
        
        
        time.sleep(1)
except KeyboardInterrupt:
    opcua_client.disconnect_from_server()