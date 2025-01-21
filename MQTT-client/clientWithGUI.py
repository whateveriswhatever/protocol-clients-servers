import asyncio
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
from threading import Thread
from gmqtt import Client as MQTTClient
import json
import csv
import io

class MQTTClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MQTT Client")
        
        # Connection variables
        self.client = None
        self.loop = asyncio.new_event_loop()
        self.connected = False
        
        # Server connection frame
        self.connection_frame = tk.LabelFrame(root, text="Broker Connection")
        self.connection_frame.pack(padx=10, pady=5, fill="x")
        
        tk.Label(self.connection_frame, text="Broker:").grid(row=0, column=0, sticky="w")
        self.broker_entry = tk.Entry(self.connection_frame, width=40)
        self.broker_entry.grid(row=0, column=1, padx=5, pady=2)
        self.broker_entry.insert(0, "test.mosquitto.org")  # Default broker
        
        tk.Label(self.connection_frame, text="Topic:").grid(row=1, column=0, sticky="w")
        self.topic_entry = tk.Entry(self.connection_frame)
        self.topic_entry.grid(row=1, column=1, padx=5, pady=2)
        self.topic_entry.insert(0, "malarkey/NBA")  # Default topic
        
        self.connect_button = tk.Button(self.connection_frame, text="Connect", command=self.connect_to_broker)
        self.connect_button.grid(row=2, column=0, padx=5, pady=5)
        
        self.disconnect_button = tk.Button(self.connection_frame, text="Disconnect", 
                                         command=self.disconnect_from_broker, state="disabled")
        self.disconnect_button.grid(row=2, column=1, padx=5, pady=5)
        
        # Message sending frame
        self.message_frame = tk.LabelFrame(root, text="Send Message")
        self.message_frame.pack(padx=10, pady=5, fill="x")
        
        tk.Label(self.message_frame, text="Format:").grid(row=0, column=0, sticky="w")
        self.format_var = tk.StringVar(value="JSON")
        format_dropdown = tk.OptionMenu(self.message_frame, self.format_var, "JSON", "CSV")
        format_dropdown.grid(row=0, column=1, sticky="w")
        
        self.message_text = tk.Text(self.message_frame, height=5, width=50)
        self.message_text.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        
        # Add default JSON message
        default_message = {
            "system_code": "123123",
            "system_name": "abcxyz",
            "device_code": "laptop",
            "device_name": "laptop1",
            "alert_type": 3,
            "content": "...",
            "note": "?"
        }
        self.message_text.insert("1.0", json.dumps(default_message, indent=2))
        
        self.send_button = tk.Button(self.message_frame, text="Send", command=self.send_message, 
                                   state="disabled")
        self.send_button.grid(row=2, column=0, pady=5)
        
        self.load_file_button = tk.Button(self.message_frame, text="Load from File", 
                                        command=self.load_from_file, state="disabled")
        self.load_file_button.grid(row=2, column=1, pady=5)
        
        # Received messages frame
        self.messages_frame = tk.LabelFrame(root, text="Received Messages")
        self.messages_frame.pack(padx=10, pady=5, fill="both", expand=True)
        
        self.message_display = scrolledtext.ScrolledText(self.messages_frame, height=10)
        self.message_display.pack(padx=5, pady=5, fill="both", expand=True)

    def on_connect(self, client, flags, rc, properties):
        """Callback when client connects to broker"""
        self.root.after(0, self.on_connection_success)

    def on_message(self, client, topic, payload, qos, properties):
        """Callback when message is received"""
        message = payload.decode()
        self.root.after(0, self.display_message, f"Received on {topic}: {message}")
        
        try:
            # Try to parse as JSON first
            data = json.loads(message)
            self.root.after(0, self.display_message, f"Parsed JSON: {json.dumps(data, indent=2)}")
        except json.JSONDecodeError:
            # If not JSON, try CSV
            try:
                csv_reader = csv.reader(io.StringIO(message))
                for row in csv_reader:
                    self.root.after(0, self.display_message, f"Parsed CSV row: {row}")
            except:
                self.root.after(0, self.display_message, "Failed to parse message as JSON or CSV")

    def connect_to_broker(self):
        """Connect to MQTT broker"""
        broker = self.broker_entry.get()
        topic = self.topic_entry.get()
        
        if not broker or not topic:
            messagebox.showerror("Error", "Broker and Topic are required!")
            return

        async def connect():
            try:
                # Create new client instance
                self.client = MQTTClient("gui-client")
                
                # Set callbacks
                self.client.on_connect = self.on_connect
                self.client.on_message = self.on_message
                
                # Connect and subscribe
                await self.client.connect(broker)
                
                await self.client.subscribe(subscription_or_topic=topic)
                
                # Keep connection alive
                while self.connected:
                    await asyncio.sleep(1)
                
            except Exception as e:
                self.root.after(0, messagebox.showerror, "Error", f"Connection failed: {str(e)}")
                self.root.after(0, self.update_gui_after_disconnect)

        self.connected = True
        Thread(target=self._run_async_task, args=(connect, )).start()
    
    def _run_async_task(self, coroutine):
        """Run async task in a loop with proper coroutine handling"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(coroutine())
    
    def on_connection_success(self):
        """Called when connection is successful"""
        self.update_gui_after_connect()
        messagebox.showinfo("Success", "Connected to broker successfully!")
        
    def disconnect_from_broker(self):
        """Disconnect from MQTT broker"""
        if self.client:
            async def disconnect():
                try:
                    await self.client.disconnect()
                except Exception as e:
                    self.root.after(0, messagebox.showerror, "Error", f"Disconnection error: {str(e)}")
                finally:
                    self.connected = False
                    self.client = None
                    self.root.after(0, self.update_gui_after_disconnect)
                    self.root.after(0, messagebox.showinfo, "Success", "Disconnected from broker!")
            
            Thread(target=self._run_async_task, args=(disconnect, )).start()
            
    def update_gui_after_connect(self):
        """Update GUI elements after connection"""
        self.connect_button["state"] = "disabled"
        self.disconnect_button["state"] = "normal"
        self.send_button["state"] = "normal"
        self.load_file_button["state"] = "normal"
        
    def update_gui_after_disconnect(self):
        """Update GUI elements after disconnection"""
        self.connect_button["state"] = "normal"
        self.disconnect_button["state"] = "disabled"
        self.send_button["state"] = "disabled"
        self.load_file_button["state"] = "disabled"
        
    def send_message(self):
        """Send message to MQTT broker"""
        if not self.client or not self.connected:
            messagebox.showerror("Error", "Not connected to broker!")
            return
            
        message = self.message_text.get("1.0", "end").strip()
        topic = self.topic_entry.get()
        
        if not message:
            messagebox.showerror("Error", "Message cannot be empty!")
            return
            
        try:
            if self.format_var.get() == "JSON":
                # Validate JSON format
                json.loads(message)
            else:
                # Validate CSV format
                csv.reader(io.StringIO(message))
                
            self.client.publish(topic, message)
            messagebox.showinfo("Success", "Message sent successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Invalid message format: {str(e)}")
            
    def load_from_file(self):
        """Load message from file"""
        format_type = self.format_var.get()
        try:
            if format_type == "JSON":
                with open("test.json", 'r') as file:
                    data = json.load(file)
                    self.message_text.delete("1.0", "end")
                    self.message_text.insert("1.0", json.dumps(data, indent=2))
            else:  # CSV
                with open("test.csv", 'r') as file:
                    self.message_text.delete("1.0", "end")
                    self.message_text.insert("1.0", file.read())
                    
            messagebox.showinfo("Success", f"Loaded {format_type} data from file!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")
            
    def display_message(self, message):
        """Display message in the GUI"""
        self.message_display.insert("end", f"{message}\n")
        self.message_display.see("end")  # Auto-scroll to bottom
        
        
if __name__ == "__main__":
    root = tk.Tk()
    gui = MQTTClientGUI(root)
    root.mainloop()