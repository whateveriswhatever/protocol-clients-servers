import asyncio
from gmqtt import Client as MQTTClient
import csv
import io
import json

# MQTT Broker settings
BROKER = "test.mosquitto.org"
TOPIC = "malarkey/NBA"
FORMAT = "JSON" # CSV or JSON

async def main():
    client = MQTTClient("client")
    
    def on_connect(client, flags, rc, properties):
        print("Connected!")
        
    def on_message(client, topic, payload, qos, properties):
        print("Received message on topic {}: {}".format(topic, payload.decode()))
        
        # Parsing CSV message
        csv_reader = csv.reader(io.StringIO(payload.decode()))
        for row in csv_reader:
            print(f"Parsed row: {row}")
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    await client.connect(BROKER)

    # Publishing data from the CSV file
    if FORMAT.upper() == "CSV":
        with open("test.csv", 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            # csv_data = csv_file.read() # Read the entire CSV file as string
        
            header = next(csv_reader, None) # Skipping the header if it exists
            for row in csv_reader:
                message = ",".join(row) # Converting row list to a CSV-formatted string
                client.publish(TOPIC, message)

                print(f"Published message: {message}!")
        
    if FORMAT.upper() == "JSON":
        with open("test.json", 'r') as json_file:
            data = json.load(json_file)
            
            for message in data:
                json_message = json.dumps(message) # Converting dict to JSON string
                client.publish(TOPIC, json_message)
                
                print("Published message: {}".format(json_message))
                
        
    # Keeping the client active for a while to allow receiving messages from the Broker
    await asyncio.sleep(20)
    await client.disconnect()

asyncio.run(main())