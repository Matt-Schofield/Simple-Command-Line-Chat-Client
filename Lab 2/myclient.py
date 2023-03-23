import sys
from ex2utils import Client, Receiver

import time

class IRCClient(Client):
    def __init__(self):
        # Call super init constructor, required in order to extend
        # __init__ and add other attributes to this class 
        Receiver.__init__(self)

        self.name = ""
        self.name_accepted = False

        self.disconnect = False

    def onMessage(self, socket, message):
        message = message.strip()

        if message == "100":
            # Name approved
            self.name_accepted = True
            return True
        
        if message == "200":
            # Disconnect approved
            self.disconnect = True
            return True

        # Remove prompt here
        # Couldn't get this to work

        # Display message
        print("\n" +message)

        # Replace prompt here
        # Couldn't get this to work either
        return True

# Parse the IP address and port you wish to connect to.
ip = sys.argv[1]
port = int(sys.argv[2])

# Create an IRC client.
client = IRCClient()

# Start server
client.start(ip, port)

# Sleep to allow time for server to display messages 
time.sleep(2)

while not client.name_accepted:
    name = input("[CLIENT] Enter a display name: ")
    client.send(name.encode())

client.name = name

while not client.disconnect:
    message = input("[" + client.name + "]: ")
    client.send(message.encode())

client.stop()
	
