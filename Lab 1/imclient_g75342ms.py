# ============================= GENERAL PRINCIPLE ==============================
# Synchronisation is achieved by a local interface for each client processing
# key value pairs on the server which act as status flags. When a sender sends a
# message, they update the server flags which notify the recipient that they are
# the new sender. The recipient meanwhile, waits and repeatedly checks the flags
# until it sees the sender has finished sending a message and that it is their
# turn to be the sender.
#
# Deadlock is prevented in this implementation, the system should never be able
# to reach a deadlock state (I hope). An example of this is in first time setup
# preventing a 'circular wait' stalemate.This is described in further detail in
# the relvant sections. Additionally, the priority system which determines who
# is a sender and who is a recipient is implemented to prevent any ambiguity
# arisng and therefore make deadlock scenarios unreachable.

# ============================= RUNNING THE CODE ===============================
# Each new client needs to be ran in it's own terminal window. There should not
# be a need to use the browser interface.
#
# At any point during a client's runtime, pressing CTRL+C will force stop the
# program. It is important to exit this way and not via CTRL+Z or closing the
# terminal window otherwise the code required for a clean exit will not run.
#
# A client is considered connected after the user has entered their name upon
# request. The first client to connect will not be able to send a message until
# another client has also connected.
#
# If a sender disconnects, the recipient will be notifed and be asked to wait
# for another client to connect.
#
# If a recipient disconnects, the sender will be notified **when they attempt to
# send the next message** and will be asked to wait for another connection.
#
# If either client disconnects, another client instance can be started. The user
# will be asked to enter their name and a new chat can begin.
#
# If both clients disconnect, ther server will be reset when the next client
# instance is started up.

# ================================== CODE ======================================

# Time - Wait functionality
# Sys - Exiting the program throught the code
# Atexit - Exiting the program cleanly
import im, time, sys, atexit

# Because the functionality of the server is limited to reading and writing
# key/value pairs, processing needs to be done in each of the clients. These
# features have been seperated out from the client component into a local
# interface. In practice, this functionality would probably be provided on and
# by the server itself.
class LocalServerInterface:
    def __init__(self):
        # Init server connection
        self.server = im.IMServerProxy('https://web.cs.manchester.ac.uk/g75342ms/comp28112_ex1/IMserver.php')
        self.tag = "SERVER"

        # Assume our client is 'second in line' for setup
        self.first_time_can_setup = False

    def reset(self):
        status = str(self.server['global_status'])[2:-1]

        # If the status doesn't exist or is CLOSED from the last instance
        # then reset the Key-Value pairs to known values
        if status == 'CLOSED' or status == '':
            # Clear all existing KV pairs
            self.server.clear()

            # Maximum connections allowed - unused currently but added so that
            # there is theoretical possibility for expansion to >2 connections
            self.server['CONNECTION_LIMIT'] = '2'
            # Keeps track of the number of clients currently connected to the
            # server
            self.server['connections'] = '0'

            # If two clients attempt to setup at the same time without the
            # following, both clients will think they are connection 1 and will
            # deadlock waiting for the other client to connect.

            # To prevent this, if the client performs the reset then it is
            # nessecarily the first client, and should be allowed to setup.
            # If another client attempts to set up in this time, it's local
            # flag it will default to false. It will then be held up further
            # down until the first client sets can_setup to TRUE and releases
            # the second client.
            self.first_time_can_setup = True
            self.server['can_setup'] = 'FALSE'

            # Clients keeps a track of the names of the clients currently
            # connected. Sender keeps track of which client is currently sending
            # a message
            self.server['clients'] = ''
            self.server['sender'] = ''

            # Used for notifiying the currenty recipient in the case where the
            # sender disconnects, informing them to wait for another client
            self.server['sender_disconnect'] = 'FALSE'

            # Used for passing the messages between the clients. The sender
            # writes to this key, and the recipient reads from it.
            self.server['last_message'] = ''

            # Can be:
            #   - OPEN - Accepting new connections
            #   - ACTIVE - Currently messaging, not accepting connections
            #   - CLOSED - Messaging closed, no longer accepting connections
            self.server['global_status'] = 'OPEN'

            # Updated when the server is reset, helpful for debugging resets.
            self.server['last_reset_timestamp'] = time.strftime("%H:%M:%S")

        print("[" + self.tag + "] Server running, last reset at", str(self.server['last_reset_timestamp'])[2:-1])

    # Initial connection processing
    def connect(self):
        print("[" + self.tag + "] Creating connection...")

        cons = int(str(self.server['connections'])[2:-1])

        # Refuse the connection attempt if connections are already maxed out or
        # if the server is not accepting connections (ACTIVE or CLOSED state)
        if cons < int(str(self.server['CONNECTION_LIMIT'])[2:-1]):
            if str(self.server['global_status'])[2:-1] == 'OPEN':
                self.client = Client(input("[" + self.tag + "] Enter name: "))
            else:
                print("[" + self.tag + "] Server not accepting connections, exiting...")
                sys.exit(0)
        else:
            print("[" + self.tag + "] Server full, exiting...")
            sys.exit(0)

        # Bind disconnect function to cleanly handle clients force disconnecting
        # via CTRL+C
        atexit.register(self.disconnect)

        print("[" + self.tag + "] Hello", self.client.name + ".")

        # The following is the implementation of holding up the second client
        # until the first has finished processing. This is only used in the
        # special case where, on first startup, 2 clients attempt to connect
        # simultaneously
        if self.first_time_can_setup == False:
            print("[" + self.tag + "] Waiting for first connection to finish processing...")

        while self.first_time_can_setup == False:
            if str(self.server['can_setup'])[2:-1] == 'TRUE':
                self.first_time_can_setup = True
                cons = int(str(self.server['connections'])[2:-1])

        # This implementation uses a 'first-come-first-served' method where the
        # first client to connect is the person who gets to send the first
        # message. Additionally update list of clients on the server.
        if cons == 0:
            print("[" + self.tag + "] You are connection 1. Please wait for another person to connect.")

            self.server['clients'] = self.client.name
            self.server['sender'] = self.client.name
        else:
            print("[" + self.tag + "] You are connection " + str(cons + 1) + ". User '" + str(self.server['clients'])[2:-1] + "' is already connected. Please wait for a message.")
            print(("=" * 34) + " CHAT " + ("=" * 34))

            self.server['global_status'] = 'ACTIVE'
            self.server['clients'] = str(self.server['clients'])[2:-1] + ',' + self.client.name

        # Increment the connection count
        cons += 1
        self.server['connections'] = str(cons)

        # Technically set by all clients, but only relevant for lines ~97-107
        self.server['can_setup'] = 'TRUE'

        self.messaging()

    # Main messaging loop
    def messaging(self):
        while True:
            # While 'we' are not the sender or we are the only connection to the
            # server, wait.
            while str(self.server['sender'])[2:-1] != self.client.name or int(str(self.server['connections'])[2:-1]) == 1:
                time.sleep(1)

                # The recipient can read the sender_disconnect key to let them
                # know if the sender has disconnected while the they are waiting
                # waiting for their turn.
                if str(self.server['sender_disconnect'])[2:-1] == 'TRUE':
                    print("[" + self.tag + "] User '" + recipient + "' disconnected.")
                    print("[" + self.tag + "] Please wait for another connection or CTRL+C to exit.")
                    self.server['sender_disconnect'] = 'FALSE'

            # Identify the name of the recipient from the server's list of
            # clients
            clients = str(self.server['clients'])[2:-1].split(',')
            clients.remove(self.client.name)
            recipient = clients[0]

            # If the last message is blank that means we are about to send the
            # first message in the chat so we notify the sender. Otherwise we
            # read the last_message key and display it to the client
            if len(self.server['last_message']) == 0:
                print("\n[" + self.tag + "] User '" + recipient + "' has connected, you are now chatting: ")
                print(("=" * 34) + " CHAT " + ("=" * 34))
            else:
                print(str(self.server['last_message'])[2:-1])

            # Get the sender client's message
            self.client.get_message()

            # If the recipient disconnected while the sender was sending their
            # message, notify the sender there message was not sent and keep
            # them as the current sender. Otherwise write to the last_message
            # key on the server and switch the recipient to the sender
            if recipient not in str(self.server['clients'])[2:-1].split(','):
                print("[" + self.tag + "] User '" + recipient + "' disconnected, your message was not sent.")
                print("[" + self.tag + "] Please wait for another connection or CTRL+C to exit.")
            else:
                self.server['last_message'] = self.client.message_out
                self.server['sender'] = recipient

    # Called when a client force disconnects with CTRL+C
    # Allows the server to accept new connections to the server without having
    # to close down and restart first.
    def disconnect(self):
        # Decrement connection count
        cons = int(str(self.server['connections'])[2:-1]) - 1
        self.server['connections'] = str(cons)

        # In the case where there is someone still connected...
        if cons == 1:
            print("[" + self.tag + "] Disconnected. \n")

            # Transfer sender privellage to them
            clients = str(self.server['clients'])[2:-1].split(',')
            clients.remove(self.client.name)
            recipient = clients[0]

            # Check if we are disconecting as a sender or a recipient
            if str(self.server['sender'])[2:-1] == self.client.name:
                self.server['sender_disconnect'] = 'TRUE'

            # Update the client list
            self.server['sender'] = recipient
            self.server['clients'] = recipient

            # Clear the last message ready for the next chat
            self.server['last_message'] = ''

            # OPEN the server to new connections
            self.server['global_status'] = 'OPEN'
        else:
            # In the case where we are the last client to disconnect we want to
            # 'tie-up' the server so it can be completely reset when a new
            # client connects
            print("[" + self.tag + "] Disconnected, closing server. \n")

            # Set status to CLOSED
            self.server['global_status'] = 'CLOSED'

            # Clear client list
            self.server['clients'] = ''



class Client:
    def __init__(self, name):
        self.name = name
        self.tag = "CLIENT"

        self.message_out = ""

    def get_message(self):
        # Message header sent along with message body so recipient can identify
        # who the message is from
        message_header = "[" + self.name.upper() + "]: "

        # Ensure the message meets the validation requirements. More constraints
        # could be added such as maximum message length, illegal characters etc.
        while True:
            message_body = input("[" + self.name.upper() + "]: ")
            if len(message_body) > 0:
                break
            else:
                print("[" + self.tag + "] Please enter a message of valid length.")

        # Join message header and message body into the final outgoing message
        self.message_out = message_header + message_body

# Initialise the server interface which will then handle creating the client and
# establshing a connection to the server.
LSI = LocalServerInterface()
LSI.reset()
LSI.connect()
