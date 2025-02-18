from opcua import Server
import random
import string
import time
from opcua_security import OPCUA_AUTHENTICATION
import bcrypt
import threading
import json
import bcrypt


server  = Server()
# authentication_system = OPCUA_AUTHENTICATION()

url = "opc.tcp://172.26.50.95:4840"
server.set_endpoint(url)

name = "OPC-UA Server"
addresspace = server.register_namespace(name)

node = server.get_objects_node()

param = node.add_object(addresspace, "H07")

node = param.add_variable(addresspace, "ExtSystemData", "")

node1 = param.add_variable(addresspace, "ExtSystemData1", "")

node.set_writable()
node1.set_writable()

USER_CREDENTIAL = {
    "admin": "loz1234"
}

def user_authentication(is_session, username, password):
    try:
        with open("credentials.json", "r") as file:
            credentials = json.load(file)

        saved_salt = credentials["salt"].encode("utf-8")
        hashed_username = bcrypt.hashpw(username.encode("utf-8"), saved_salt).decode()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), saved_salt).decode()

        return (
            hashed_username == credentials["username"]
            and hashed_password == credentials["password"]
        )

    except FileNotFoundError:
        print("Authentication file not found.")
        return False

# server.user_manager.set_user_manager(user_authentication)

server.start()
print("Server started at: {}".format(url))

#authentication_system.init_authentication("172.26.50.95")
#authentication_system.set_server_credential("admin", "loz1234")

print("Node address of ExtSystemData: {}".format(node.nodeid))
print("Node address of ExtSystemData1: {}".format(node1.nodeid))

def generate_random_string(length):
    character_set = string.ascii_letters + string.digits
    
    random_string = ''.join(random.choice(character_set) for _ in range(length))
    
    return random_string

x = 0

# Set user authentication
server.user_manager.set_user_manager(user_authentication)

def update_node_value():
    x = 0
    while True:
        random_str = generate_random_string(x)
        print(f"Updating Node Value: {random_str}")
        node.set_value(random_str)
        
        x += 1
        time.sleep(1)

# Run data updates in a separate thread
# update_thread = threading.Thread(target=update_node_value, daemon=True)
# update_thread.start()

try:
    while True:
        time.sleep(1)
        
except KeyboardInterrupt:
    print("Stopped the server!")
    server.stop()
    
    