import asyncio
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from threading import Thread
import json
import csv
import logging
from clientTesting1 import UAClient

# Configure logging
logging.basicConfig(level=logging.INFO)

class OPCUAClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OPC-UA Client")
        
        # Connection variables
        self.client = None
        self.loop = asyncio.new_event_loop()
        self.subscription = None
        
        # Server connection frame
        self.connection_frame = tk.LabelFrame(root, text="Server Connection")
        self.connection_frame.pack(padx=10, pady=5, fill="x")
        
        tk.Label(self.connection_frame, text="Endpoint:").grid(row=0, column=0, sticky="w")
        self.endpoint_entry = tk.Entry(self.connection_frame, width=40)
        self.endpoint_entry.grid(row=0, column=1, padx=5, pady=2)
        self.endpoint_entry.insert(0, "opc.tcp://127.0.0.1:4840")  # Default value
        
        tk.Label(self.connection_frame, text="Username:").grid(row=1, column=0, sticky="w")
        self.username_entry = tk.Entry(self.connection_frame)
        self.username_entry.grid(row=1, column=1, padx=5, pady=2)
        self.username_entry.insert(0, "admin")  # Default value
        
        tk.Label(self.connection_frame, text="Password:").grid(row=2, column=0, sticky="w")
        self.password_entry = tk.Entry(self.connection_frame, show="*")
        self.password_entry.grid(row=2, column=1, padx=5, pady=2)
        self.password_entry.insert(0, "loz1234")  # Default value
        
        self.connect_button = tk.Button(self.connection_frame, text="Connect", command=self.connect_to_server)
        self.connect_button.grid(row=3, column=0, padx=5, pady=5)
        
        self.disconnect_button = tk.Button(self.connection_frame, text="Disconnect", command=self.disconnect_from_server, state="disabled")
        self.disconnect_button.grid(row=3, column=1, padx=5, pady=5)
        
        # Message sending frame
        self.message_frame = tk.LabelFrame(root, text="Send Message")
        self.message_frame.pack(padx=10, pady=5, fill="x")
        
        tk.Label(self.message_frame, text="Format:").grid(row=0, column=0, sticky="w")
        self.format_var = tk.StringVar(value="json")
        format_dropdown = tk.OptionMenu(self.message_frame, self.format_var, "json", "csv")
        format_dropdown.grid(row=0, column=1, sticky="w")
        
        self.message_text = tk.Text(self.message_frame, height=5, width=50)
        self.message_text.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        
        # Add default JSON message
        default_message = {
            "system_code": "CLIENT002",
            "system_name": "Client B",
            "device_code": "Device Z",
            "device_name": "poipopzzz",
            "alert_type": 3,
            "alert_content": "Client 2 test message",
            "note": "Sent from client 2"
        }
        self.message_text.insert("1.0", json.dumps(default_message, indent=2))
        
        self.send_button = tk.Button(self.message_frame, text="Send", command=self.send_message, state="disabled")
        self.send_button.grid(row=2, column=0, columnspan=2, pady=5)
        
        # Subscription frame
        self.subscription_frame = tk.LabelFrame(root, text="Received Messages")
        self.subscription_frame.pack(padx=10, pady=5, fill="x")
        
        self.message_display = scrolledtext.ScrolledText(self.subscription_frame, height=10, state="disabled")
        self.message_display.pack(padx=5, pady=5, fill="both")

        # Add file sending frame after message frame
        self.file_frame = tk.LabelFrame(root, text="Send File Data")
        self.file_frame.pack(padx=10, pady=5, fill="x")
        
        self.file_path_var = tk.StringVar()
        self.file_path_entry = tk.Entry(self.file_frame, textvariable=self.file_path_var, width=40)
        self.file_path_entry.grid(row=0, column=0, padx=5, pady=2)
        
        self.browse_button = tk.Button(self.file_frame, text="Browse", command=self.browse_file)
        self.browse_button.grid(row=0, column=1, padx=5, pady=2)
        
        self.send_file_button = tk.Button(self.file_frame, text="Send File Data", command=self.send_file_data, state="disabled")
        self.send_file_button.grid(row=1, column=0, columnspan=2, pady=5)

    def browse_file(self):
        """Open file dialog to select JSON or CSV file"""
        filetypes = [
            ('JSON files', '*.json'),
            ('CSV files', '*.csv')
        ]
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            self.file_path_var.set(filename)

    def read_json_file(self, file_path):
        """Read and parse JSON file"""
        with open(file_path, 'r') as file:
            return json.load(file)

    def read_csv_file(self, file_path):
        """Read CSV file row by row, skipping header"""
        with open(file_path, 'r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                if row:  # Skip empty lines
                    yield row

    def send_file_data(self):
        """Send all data from selected file"""
        if not self.client:
            messagebox.showerror("Error", "Not connected to the server!")
            return

        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showerror("Error", "Please select a file first!")
            return

        async def send_multiple():
            try:
                message_sent = 0
                total_messages = 0
                
                
                # Determine file type
                if file_path.endswith('.json'):
                    with open(file_path, 'r') as file:
                        data = json.load(file)
                    if not isinstance(data, list):
                        data = [data]  # Convert single object to list
                    
                    total_messages = len(data)    
                    for idx, message in enumerate(data, 1):
                        # Adding a unique identifier to each message
                        message["message_id"] = f"msg_{idx}"
                        message["total_message"] = total_messages
                        
                        # Sending each message with increased delay
                        await self.client.send_message(message, "json")
                        message_sent += 1
                        
                        self.root.after(0, self.display_message, f"Sent message {idx}/{total_messages}: {json.dumps(message)[:100]}...")
                        
                        # Increased delay to ensure proper processing
                        await asyncio.sleep(3) # 3 seconds delay between each message
                        
                        
                elif file_path.endswith(".csv"):
                    
                    # Counting total rows in advanced
                    with open(file_path, 'r') as file:
                        total_messages = sum(1 for row in csv.reader(file)) - 1 # Substracting the header
                    
                    with open(file_path, 'r') as file:
                        csv_reader = csv.reader(file)
                        next(csv_reader)  # Skip header
                        for idx, row in enumerate(csv_reader, 1):
                            if row:  # Skip empty lines
                                message = ','.join(row)  # Convert each CSV row to a string
                                logging.info(f"Sending message {idx}: {message}")
                                await self.client.send_message(message, "csv")
                                message_sent += 1
                                
                                self.root.after(0, self.display_message, f"Sent message {idx}/{total_messages}")
                                
                                await asyncio.sleep(3)  # Increased delay to ensure proper processing
                else:
                    raise ValueError("Unsupported file type!!!")

                self.root.after(0, messagebox.showinfo, "Success", "Successfully sent all messages!")
            except Exception as e:
                logging.error(f"Failed to send file data: {str(e)}")
                self.root.after(0, messagebox.showerror, "Error", f"Failed to send file data: {str(e)}\nMessage sent: {message_sent}/{total_messages}")

        Thread(target=self.run_async_task, args=(send_multiple(),)).start()

    def update_gui_after_connect(self):
        """Update GUI elements after successful connection"""
        self.connect_button["state"] = "disabled"
        self.disconnect_button["state"] = "normal"
        self.send_button["state"] = "normal"
        self.send_file_button["state"] = "normal"  # Enable file sending button

    def update_gui_after_disconnect(self):
        """Update GUI elements after disconnection"""
        self.connect_button["state"] = "normal"
        self.disconnect_button["state"] = "disabled"
        self.send_button["state"] = "disabled"
        self.send_file_button["state"] = "disabled"  # Disable file sending button

    async def message_callback(self, message):
        """Callback function for received messages"""
        try:
            if isinstance(message, dict):
                displayed_text = f"Received message {message.get("message_id", "unknown")}: {json.dumps(message)[:100]}..."
            else:
                displayed_text = f"Received: {message}"
            
            self.root.after(0, self.display_message, displayed_text)
        except Exception as ex:
            logging.error(f"Error in message callback: {str(ex)}")
            
            self.root.after(0, self.display_message, f"Received: {message}")

    async def setup_subscription(self):
        """Set up subscription after connection"""
        self.subscription = await self.client.subscribe_to_messages(self.message_callback)

    def connect_to_server(self):
        endpoint = self.endpoint_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not endpoint or not username or not password:
            messagebox.showerror("Error", "All fields are required!")
            return
        
        async def connect():
            try:
                self.client = UAClient(endpoint, username, password)
                await self.client.connect()
                await self.setup_subscription()
                self.root.after(0, self.update_gui_after_connect)
                messagebox.showinfo("Success", "Connected to server successfully!")
            except Exception as e:
                self.root.after(0, messagebox.showerror, "Error", f"Connection failed: {str(e)}")
                self.root.after(0, self.update_gui_after_disconnect)
        
        Thread(target=self.run_async_task, args=(connect(),)).start()

    def update_gui_after_connect(self):
        """Update GUI elements after successful connection"""
        self.connect_button["state"] = "disabled"
        self.disconnect_button["state"] = "normal"
        self.send_button["state"] = "normal"
        self.send_file_button["state"] = "normal"

    def update_gui_after_disconnect(self):
        """Update GUI elements after disconnection"""
        self.connect_button["state"] = "normal"
        self.disconnect_button["state"] = "disabled"
        self.send_button["state"] = "disabled"
        self.send_file_button["state"] = "disabled"

    def disconnect_from_server(self):
        if self.client:
            async def disconnect():
                await self.client.disconnect()
                self.client = None
                self.subscription = None
                self.root.after(0, self.update_gui_after_disconnect)
                messagebox.showinfo("Success", "Disconnected from server!")
            
            Thread(target=self.run_async_task, args=(disconnect(),)).start()

    def send_message(self):
        if not self.client:
            messagebox.showerror("Error", "Not connected to the server!")
            return
        
        format_type = self.format_var.get()
        message = self.message_text.get("1.0", "end").strip()
        
        if not message:
            messagebox.showerror("Error", "Message cannot be empty!")
            return
        
        async def send():
            try:
                data = json.loads(message) if format_type == "json" else message
                await self.client.send_message(data, format_type)
                messagebox.showinfo("Success", "Message sent successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send message: {str(e)}")
        
        Thread(target=self.run_async_task, args=(send(),)).start()

    def display_message(self, message):
        """Display received message in the GUI"""
        self.message_display["state"] = "normal"
        self.message_display.insert("end", f"{message}\n")
        self.message_display.see("end")  # Auto-scroll to bottom
        self.message_display["state"] = "disabled"

    def run_async_task(self, task):
        """Run async task in the event loop"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(task)

if __name__ == "__main__":
    root = tk.Tk()
    gui = OPCUAClientGUI(root)
    root.mainloop()