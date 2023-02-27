# Store S/R info on server or on client?

# 0) Server inits with no clients and no K/V pairs
# 1) Client A connects to server, checks if is the first connection
# 2) It is so it becomes the sender, and waits for server to be in ready state
# 3) Client B connects, checks if is the first connection
# 4) It is not so it becomes the recipient, notifies server
# 5) Server enters ready state, waits for A to send a message
# 6) Recieves and updates message, sets status code to OK
# 7) Reverses roles, B is now the sender and A is the recipient
#
# Clients wait and check at regular intervals for server state
# Recipient clients who attempt to send a message (set a key) will see a status code of INVALID and the message will be discarded

# Init server connection
import im, time, sys

class LocalServerInterface:
    def __init__(self):
        self.server = im.IMServerProxy('https://web.cs.manchester.ac.uk/g75342ms/comp28112_ex1/IMserver.php')
        self.tag = "SERVER"

    def reset(self):
        status = str(self.server['global_status'])[2:-1]

        # If the status doesn't exist or is is ACTIVE we need to prepare/reset
        # the keys required to handle the messaging service
        # If the status is OPEN then we assume it is already set up
        if status != 'OPEN':
            self.server.clear()

            self.server['CONNECTION_LIMIT'] = '2'
            self.server['connections'] = '0'

            self.server['clients'] = ''
            self.server['sender'] = ''

            self.server['last_message'] = ''

            # Can be...
            #   - OPEN - Accepting new connections
            #   - ACTIVE - Currently messaging, not accepting connections
            self.server['global_status'] = 'OPEN'

            self.server['last_reset_timestamp'] = time.strftime("%H:%M:%S")

        print("[" + self.tag + "] Server running, last reset at", str(self.server['last_reset_timestamp'])[2:-1])

    def connect(self):
        print("[" + self.tag + "] Creating connection...")

        cons = int(str(self.server['connections'])[2:-1])

        if int(str(self.server['connections'])[2:-1]) < int(str(self.server['CONNECTION_LIMIT'])[2:-1]):
            self.client = Client(input("[" + self.tag + "] Enter name: "))
        else:
            print("[" + self.tag + "] Server full, exiting...")
            sys.exit(0)

        print("[" + self.tag + "] Hello", self.client.name + ".")

        if cons == 0:
            print("[" + self.tag + "] You are connection 1. Please wait for another person to connect.")

            self.server['clients'] = self.client.name
            self.server['sender'] = self.client.name
        else:
            print("[" + self.tag + "] You are connection " + str(cons + 1) + ". User '" + str(self.server['clients'])[2:-1] + "' is already connected. Please wait for a message. \n")
            print(("=" * 34) + " CHAT " + ("=" * 34))

            self.server['global_status'] = 'ACTIVE'
            self.server['clients'] = str(self.server['clients'])[2:-1] + ',' + self.client.name

        cons += 1
        self.server['connections'] = str(cons)

        self.messaging()

    def messaging(self):
        while True:
            while str(self.server['sender'])[2:-1] != self.client.name or int(str(self.server['connections'])[2:-1]) == 1:
                time.sleep(1)

            clients = str(self.server['clients'])[2:-1].split(',')
            clients.remove(self.client.name)
            recipient = clients[0]

            if len(self.server['last_message']) == 0:
                print("[" + self.tag + "] User '" + recipient + "' has connected, you are now chatting: \n")
                print(("=" * 34) + " CHAT " + ("=" * 34))
            else:
                print(str(self.server['last_message'])[2:-1])

            self.client.get_message()
            self.server['last_message'] = self.client.message_out

            self.server['sender'] = recipient

class Client:
    def __init__(self, name):
        self.name = name
        self.tag = "CLIENT"

        self.message_out = ""

    def get_message(self):
        message_header = "[" + self.name.upper() + "]: "

        while True:
            message_body = input("[" + self.name.upper() + "]: ")
            if len(message_body) > 0:
                break
            else:
                print("[" + self.tag + "] Please enter a message of valid length.")

        self.message_out = message_header + message_body

# CONNECTION SHOULD CEASE IF PROGRAM TERMINATES
# If two clients attempt to connect before the connection incr. then both clients will think they are the only one connected

LSI = LocalServerInterface()
LSI.reset()
LSI.connect()
