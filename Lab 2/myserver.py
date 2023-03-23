import sys, time
from ex2utils import Server

# Create an echo server class
class EchoServer(Server):

    def onStart(self):
        print("Server started at " + time.strftime("%H:%M:%S"))
        print("SERVER LOG:")
        print("=" * 10)

        # List of all available command words
        self.COMMANDS = ["ping", "users", "whisper", "all", "help", "disconnect"]

        # No initial connections
        self.connections = 0

        # Reserve certain names so users cannot impersonate other roles
        self.CLIENT_NAME_BLACKLIST = ["admin"]
        self.client_names = []

        # Stored to enable messaging and server notifications 
        self.client_sockets = []
        
    def onConnect(self, socket):
        socket.name = ""
        socket.assigned_name = False

        socket.send("[SERVER] You are now connected".encode())
        socket.send("[SERVER] (TELNET CLIENT ONLY) Take care when typing inputs, if backspace, arrow keys, or similar are pressed the server will be unable to process it correctly".encode())

        self.connections += 1
        print("[" + time.strftime("%H:%M:%S") + "] New client is connecting. " + str(self.connections) + " connections are now open.")
        
        
    def onMessage(self, socket, message):
        print("[" + time.strftime("%H:%M:%S") + "] Message recieved from " + (socket.name.upper() if socket.assigned_name == True else "connecting client"))

        message_array = message.strip().split(' ')

        if socket.assigned_name == False:
            name = message.strip().lower()
            # Check the name is valid
            if not name.isalnum() or len(name) > 8 :
                socket.send("[SERVER] Names should contain alphanumeric characters only and be at most 8 characters long".encode())
            elif name in self.client_names:
                socket.send("[SERVER] Name is already taken (names are case insensitive)".encode())
            elif name in self.CLIENT_NAME_BLACKLIST:
                socket.send("[SERVER] Protected name is not allowed".encode())
            else:
                # Name is valid, set socket values
                socket.name = name
                socket.assigned_name = True
                
                # Set server values 
                self.client_names.append(name)
                self.client_sockets.append(socket)

                self.sendToUser("100", socket.name, hidden=True)

                print("[" + time.strftime("%H:%M:%S") + "] Client '" + name.upper() + "' connected. ")
                self.sendToAll("User " + name.upper() + " has connected. There are " + str(self.connections - 1) + " other people connected.")

            return True

        if message_array[0].startswith('/'):
            command = message_array[0][1:].lower()
            params = message_array[1:]

            print("[" + time.strftime("%H:%M:%S") + "] Command recieved - Command: " + command + ", Parameters: " + ', '.join(message_array[1:]))

            return self.processCommand(socket, command, params)

        self.sendToAll(' '.join(message_array), socket.name)
        return True

    def processCommand(self, socket, command, params):
        if command == "ping":
            self.sendToUser("Pong, connected to server.", socket.name)
            return True

        if command == "users":
            self.sendToUser("Connected users: " + ', '.join(self.client_names), socket.name)
            return True
        
        if command == "help":
            self.sendToUser(""" 
            Available commands:
                /ping - Should recieve 'pong' back from the server. Can be used to check if you are succesfully connected 
                /users - Get names of all the currently connected clients
                /help - Display this help message
                /all <message> - Send a message to all users
                /whisper <user> <message> - Send a private message to a specified user, private messages can only be seen by you and the specified recipient
                /disconnect - Disconnects from the server.
                """, socket.name)
            return True

        if command == "all":
            if len(params) < 1:
                self.sendToUser("Correct usage: /all <message>", socket.name)
            else:
                self.sendToAll(' '.join(params), socket.name)
            return True
    

        if command == "whisper":
            if len(params) < 2:
                self.sendToUser("Correct usage: /whisper <user> <message>", socket.name)
            else:
                target_user = params[0]
                target_message = ' '.join(params[1:])
                self.sendToUser(target_message, target_user, socket.name)
            return True

        if command == "disconnect":
            self.sendToUser("Disconnecting from server", socket.name)
            self.sendToAll("User " + socket.name + " has disconnected.")
            
            return False
        
        # Provided command was not recognised
        self.sendToUser("[SERVER] Command '" + command + "' was not recognised.", socket.name)
        print("[" + time.strftime("%H:%M:%S") + "] Command '" + command + "' was not recognised.")
        return True
        
    def sendToAll(self, message_body, sender=None):
        tag = ""
        
        if sender == None:
            tag = "[SERVER]"
        else:
            tag = "[" + sender.upper() + "]"

        message = (tag + " " + message_body).encode()

        for client in self.client_sockets:
            if client.name != sender:
                client.send(message)

        return True

    def sendToUser(self, message_body, recipient, sender=None, hidden=False):
        tag = ""

        if sender == None:
            tag = "[SERVER]"
        else:
            tag = "[PRIVATE - " + sender.upper() + "]"

        message = (tag + " " + message_body).encode()

        for client in self.client_sockets:
            if client.name == recipient:
                if hidden == True:
                    # If hidden just send the message body and the client will know not to dispaly it
                    client.send(message_body.encode())
                else:
                    client.send(message)   
                return True
            
        # If code is here then recipient was not found so notify the sender
        # If the private message was sent by server in this case the recipient 
        # will almost always be connected so getting to this point is unlikely
        if sender != None:
            for client in self.client_sockets:
                if client.name == sender:
                    client.send(("User " + recipient.upper() + " is not currently connected, your message was not sent.").encode())

        return False

    def onDisconnect(self, socket):
        self.sendToUser("200", socket.name, hidden=True)
        
        self.connections -= 1
        print("[" + time.strftime("%H:%M:%S") + "] User " + socket.name + " disconnected. " + str(self.connections) + " clients now connected.")
        self.client_names.remove(socket.name)
        self.client_sockets.remove(socket)
        
	
# Parse the IP address and port you wish to listen on.
ip = sys.argv[1]
port = int(sys.argv[2])

# Create an echo server.
server = EchoServer()

# Start server
server.start(ip, port)