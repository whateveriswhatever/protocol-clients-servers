import asyncio
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from gmqtt import Client as MQTTClient
import csv
import io
import json
import asyncio
from asyncio import get_event_loop
from functools import partial
import threading
import os

class MQTTClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MQTT Client")
        self.client = None
        self.is_connected = False
        self.selected_file = None
        
        # Connection Frame
        conn_frame = ttk.LabelFrame(root, text="Connection Settings", padding="5")
        conn_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        ttk.Label(conn_frame, text="Broker:").grid(row=0, column=0, padx=5, pady=5)
        self.broker_entry = ttk.Entry(conn_frame)
        self.broker_entry.insert(0, "test.mosquitto.org")
        self.broker_entry.grid(row=0, column=1, padx=5, pady=5)
        
        self.connect_button = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.connect_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Subscription Frame
        sub_frame = ttk.LabelFrame(root, text="Subscription", padding="5")
        sub_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        ttk.Label(sub_frame, text="Topic:").grid(row=0, column=0, padx=5, pady=5)
        self.topic_entry = ttk.Entry(sub_frame)
        self.topic_entry.insert(0, "malarkey/NBA")
        self.topic_entry.grid(row=0, column=1, padx=5, pady=5)
        
        self.subscribe_button = ttk.Button(sub_frame, text="Subscribe", command=self.subscribe, state="disabled")
        self.subscribe_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Manual Message Publishing Frame
        manual_pub_frame = ttk.LabelFrame(root, text="Send Message", padding="5")
        manual_pub_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        ttk.Label(manual_pub_frame, text="Message:").grid(row=0, column=0, padx=5, pady=5)
        self.message_entry = ttk.Entry(manual_pub_frame, width=40)
        self.message_entry.grid(row=0, column=1, padx=5, pady=5)
        
        self.send_button = ttk.Button(manual_pub_frame, text="Send", command=self.send_message, state="disabled")
        self.send_button.grid(row=0, column=2, padx=5, pady=5)
        
        # File Publishing Frame
        pub_frame = ttk.LabelFrame(root, text="Publish From File", padding="5")
        pub_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        self.format_var = tk.StringVar(value="JSON")
        ttk.Radiobutton(pub_frame, text="JSON", variable=self.format_var, value="JSON").grid(row=0, column=0, padx=5)
        ttk.Radiobutton(pub_frame, text="CSV", variable=self.format_var, value="CSV").grid(row=0, column=1, padx=5)
        
        # Add label to show selected file
        self.file_label = ttk.Label(pub_frame, text="No file selected")
        self.file_label.grid(row=0, column=2, padx=5)
        
        self.file_button = ttk.Button(pub_frame, text="Select File", command=self.select_file, state="disabled")
        self.file_button.grid(row=0, column=3, padx=5, pady=5)
        
        self.publish_button = ttk.Button(pub_frame, text="Publish File", command=self.publish_messages, state="disabled")
        self.publish_button.grid(row=0, column=4, padx=5, pady=5)
        
        # Messages Frame
        msg_frame = ttk.LabelFrame(root, text="Messages", padding="5")
        msg_frame.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        
        self.messages_text = scrolledtext.ScrolledText(msg_frame, width=50, height=20)
        self.messages_text.grid(row=0, column=0, padx=5, pady=5)
        
        # Configure grid weights
        root.grid_rowconfigure(4, weight=1)
        root.grid_columnconfigure(0, weight=1)
        
        # Initialize asyncio loop
        self.loop = asyncio.new_event_loop()
        self.thread = None

    def toggle_connection(self):
        if not self.is_connected:
            self.connect()
        else:
            self.disconnect()

    def connect(self):
        self.thread = threading.Thread(target=self.run_async_loop, daemon=True)
        self.thread.start()

    def run_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect_mqtt())

    async def connect_mqtt(self):
        self.client = MQTTClient("gui-client")
        
        def on_connect(client, flags, rc, properties):
            self.root.after(0, self.handle_connect)
            
        def on_message(client, topic, payload, qos, properties):
            message = f"Received on {topic}: {payload.decode()}\n"
            self.root.after(0, lambda: self.messages_text.insert(tk.END, message))
            self.root.after(0, lambda: self.messages_text.see(tk.END))
            
        def on_disconnect(client, packet, exc=None):
            self.root.after(0, self.handle_disconnect)
        
        self.client.on_connect = on_connect
        self.client.on_message = on_message
        self.client.on_disconnect = on_disconnect
        
        await self.client.connect(self.broker_entry.get())

    def handle_connect(self):
        self.is_connected = True
        self.connect_button.config(text="Disconnect")
        self.subscribe_button.config(state="normal")
        self.file_button.config(state="normal")
        self.send_button.config(state="normal")
        self.messages_text.insert(tk.END, "Connected to broker!\n")
        self.messages_text.see(tk.END)

    def handle_disconnect(self):
        self.is_connected = False
        self.connect_button.config(text="Connect")
        self.subscribe_button.config(state="disabled")
        self.file_button.config(state="disabled")
        self.publish_button.config(state="disabled")
        self.send_button.config(state="disabled")
        self.messages_text.insert(tk.END, "Disconnected from broker!\n")
        self.messages_text.see(tk.END)

    def disconnect(self):
        if self.client:
            asyncio.run_coroutine_threadsafe(self.client.disconnect(), self.loop)

    def subscribe(self):
        topic = self.topic_entry.get()
        if self.client and topic:
            self.client.subscribe(topic)
            self.messages_text.insert(tk.END, f"Subscribed to {topic}\n")
            self.messages_text.see(tk.END)

    def send_message(self):
        if not self.client or not self.is_connected:
            messagebox.showerror("Error", "Not connected to broker!")
            return
            
        message = self.message_entry.get()
        if message:
            topic = self.topic_entry.get()
            self.client.publish(topic, message)
            self.messages_text.insert(tk.END, f"Sent message: {message}\n")
            self.messages_text.see(tk.END)
            self.message_entry.delete(0, tk.END)  # Clear the message entry

    def select_file(self):
        file_types = [('JSON files', '*.json'), ('CSV files', '*.csv')] if self.format_var.get() == "JSON" else [('CSV files', '*.csv'), ('JSON files', '*.json')]
        filename = filedialog.askopenfilename(filetypes=file_types)
        if filename:
            self.selected_file = filename
            self.file_label.config(text=os.path.basename(filename))
            self.publish_button.config(state="normal")
            self.messages_text.insert(tk.END, f"Selected file: {filename}\n")
            self.messages_text.see(tk.END)

    def publish_messages(self):
        if not self.client or not self.is_connected:
            messagebox.showerror("Error", "Not connected to broker!")
            return
            
        if not self.selected_file or not os.path.exists(self.selected_file):
            messagebox.showerror("Error", "Please select a valid file first!")
            return
            
        try:
            if self.format_var.get() == "CSV":
                with open(self.selected_file, 'r') as csv_file:
                    csv_reader = csv.reader(csv_file)
                    header = next(csv_reader, None)  # Skip header if exists
                    for row in csv_reader:
                        message = ",".join(row)
                        self.client.publish(self.topic_entry.get(), message)
                        self.messages_text.insert(tk.END, f"Published: {message}\n")
                        self.messages_text.see(tk.END)
                        self.root.update()  # Update GUI to show progress
            else:  # JSON
                with open(self.selected_file, 'r') as json_file:
                    try:
                        data = json.load(json_file)
                        if isinstance(data, list):
                            for item in data:
                                json_message = json.dumps(item)
                                self.client.publish(self.topic_entry.get(), json_message)
                                self.messages_text.insert(tk.END, f"Published: {json_message}\n")
                                self.messages_text.see(tk.END)
                                self.root.update()  # Update GUI to show progress
                        else:
                            json_message = json.dumps(data)
                            self.client.publish(self.topic_entry.get(), json_message)
                            self.messages_text.insert(tk.END, f"Published: {json_message}\n")
                            self.messages_text.see(tk.END)
                    except json.JSONDecodeError as e:
                        messagebox.showerror("Error", f"Invalid JSON file: {str(e)}")
                        return
                        
            self.messages_text.insert(tk.END, "File publishing completed!\n")
            self.messages_text.see(tk.END)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error publishing file: {str(e)}")

def main():
    root = tk.Tk()
    app = MQTTClientGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()