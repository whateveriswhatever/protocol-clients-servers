# Publisher Client
from opcua import Client
import time
import csv
import json

class OPCUA_Publisher:
    def __init__(self, server_url, node_id):
        self.client = Client(server_url)
        self.node_id = node_id

    def connect(self):
        self.client.connect()
        self.node = self.client.get_node(self.node_id)
        print("Connected to OPC UA Server as Publisher")

    def send_data_from_csv_file(self, csv_file_path):
        with open(csv_file_path, 'r') as file:
            try:
                reader = csv.reader(file)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) > 0:
                        data = ','.join(row)
                        self.node.set_value(data)
                        print(f"Published: {data}")
                        time.sleep(1)
            finally:
                file.close()
    
    def send_data_from_json_file(self, json_file_path):
        with open(json_file_path, 'r') as file:
            try:
                data = json.load(file)
                storage = list(data)
                for json_obj in storage:
                    json_str = json.dumps(json_obj)
                    self.node.set_value(json_str)
                    print(f"Publised: {json_str}")
                    time.sleep(1)
            finally:
                file.close()

    def disconnect(self):
        self.client.disconnect()
        print("Publisher Disconnected")

##############################################################################################

# Subscriber Client
def subscriber_callback(node, value, data):
    print(f"[Subscriber] Received: {value}")

class OPCUA_Subscriber:
    def __init__(self, server_url, node_id):
        self.client = Client(server_url)
        self.node_id = node_id

    def connect(self):
        self.client.connect()
        self.node = self.client.get_node(self.node_id)
        self.subscription = self.client.create_subscription(100, self)
        self.subscription.subscribe_data_change(self.node)
        print("Connected to OPC UA Server as Subscriber")

    def datachange_notification(self, node, val, data):
        #print(f"[Subscriber] Received update: {val}")
        pass

    def disconnect(self):
        self.client.disconnect()
        print("Subscriber Disconnected")

if __name__ == "__main__":
    defined_nodeID = input("Enter node ID for publisher and subscriber: ")
    
    publisher = OPCUA_Publisher("opc.tcp://172.26.50.95:4840", defined_nodeID)
    subscriber = OPCUA_Subscriber("opc.tcp://172.26.50.95:4840", defined_nodeID)

    try:
        publisher.connect()
        subscriber.connect()

        # Simulate PubSub behavior from CSV
        for i in range(0, 10, 1):
            print("*", end='')
        print("\n\t Option 1: Sending an JSON file to OPC-UA server")
        print("\t Option 2: Sending an CSV file to OPC-UA server")
        
        selected_option = int(input("\nEnter your choice: "))
        
        if selected_option == 1:
            filePath = str(input("Enter the JSON file path: "))
            publisher.send_data_from_json_file(filePath)
        
        if selected_option == 2:
            filePath = str(input("Enter the CSV file path: "))
            publisher.send_data_from_csv_file(filePath)
    
    except KeyboardInterrupt:
        pass
    finally:
        publisher.disconnect()
        subscriber.disconnect()
