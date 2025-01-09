# Python Chat Client

Two versions of a python based messaging client using a key-value dictionary store to act as a 'server'.

## Structure

Each 'lab' folder follows a given task as part of a 'Distributed Systems' module. The general point of the exercise was to demonstrate the potential faults that can occur when communicating over a network.

In both cases the objective was to create a 'protocol' for a chat client that could handle a variety of error codes. Lab 1 uses a PHP script to act as a very rudimentary server, offering Read/Writeable key-value pairs allowing each client to communicate indirectly by listening to changes. The PHP must be hosted on a server, and currently the program is configured to access university hosting, which I no longer have access to. For this reason the program will not be able to run until I get round to changing the hosting method.

The second client used a socket based server instead. This wass less restrictive than the first task, and is also able to handle >2 connections at a time. This chat supports dynamic connects and disconnects by clients, and allows both public and private messaging via a 'whisper' command. A more in depth description is provided below.

## Lab 2 Description
The protocol description was written with two parts in mind, with and without the 'custom client' (myclient.py). Certain features such as replies and a correctly formatted UI are only available in the custom client, as I am unable to effectively implement these in the 'pre-made' telnet client

### Setup
Initially, when the server starts, it sets up server level variables to help track and manage clients. These include a list of available commands (each discussed in detail further down) that clients can use, and a connection counter to track how many clients are connected at any given moment. These are used to determine how many clients an incoming message needs to be sent to, and can also be used to handle potential connection limits. 

Additionally there is an (initially empty) array of client names and a constant blacklist array which new client names will be checked against in order to prevent random users from obtaining already in use names, or common role specific names (such as 'admin') to prevent impersonation.

### Commands
Available commands (All commands are preceeded with a '/' character and parameters are denoted inside '<>'):
```
/ping - Expects a message "pong" back from the server. Allows client to check if they are succesfully connected 
/users - Expects a list of display names of all the currently connected clients, obtained from the the servers client names array described above
/help - Displays all the available commands a user can use to the client. Displays a similar message to this description.
/all <message> - Send a message to all currently connected clients. These messages can be seen by everyone
/whisper <user> <message> - Send a private message to a specified user, private messages should only be seen by the sender and specified recipient
/reply <message> - Reply with a message to the last user that sent the client a private message, again private messages should only be seen by the sender and recipients. This feature will only be available in the custom client, not the telnet client.
/disconnect - Disconnects the user from the server.
```

### Connection / Registration
When a client connects the server will ask them for a display name. Any messages the connecting users sends in this time will be interpreted as providing a display name and will not be shown to any other users. Names will be checked against the existing list of display names and the blacklist of names that are not allowed. When a suitable and free name is provided, it will be added to the display name list. All other users will be notified that a new user has connected and what their name is and the client will now be able to message. Unlike the first iteration of the messaging server, the server should theoretically have no problem servicing multiple registration sequences at the same time and should not require any additional code to handle this case.

### Messaging
When a message is sent by a connected client, the message first needs to be processed. White space and control characters are stripped from the message and there is a check to see if there is a preceeding '/' chracter, indicating that the user entered a command.

If the message was not a command, the server assumes the user intends to send a global message. In effect this is identical to sending a message via the '/all' command (Side note: I did consider using a channel system and having the user use /all and /whisper to switch between private and public messaging modes, but decided this would add unessecary complexity). The message is combined with the users display name, ready to be sent off to all other connected clients. The server will iterate over every connected client and send the message to them. The sender may see their message dupliacted for the time being - until I move on to implementing my own version of the client, the options to edit the display of the messaging UI is limited.

In the alternative case where the message was a command, the provided command name is checked against the available commands and further checks are done to ensure the correct paramters (if applicable) are provided. A suitable response message is constructed based on the provided command, and the user is notified if the command was formatted incorrectly, or if the command wasn't recognised by the server.

In the case of private messaging, assuming the command is of the correct form, the server will check if the intended recipient specified is connected by checking if the name appears in the list of connected client names. if they are a message is sent directly, and only, to them. Additionally, with the custom client, the recipient of a private message will be able to store the name of the user that sent them the last private message and then they can use the '/reply' command to send another private message back to them without having to specify a target user. The process for replies is the same, as the initial sender may have disconnected during the time it takes for the recipient to send a reply.

### Disconnect
This process is effectively the reverse of the registration sequence. All other connected users are notfied of the client's disconnect, and then user's disaply name is removed from the available list of client names and the connection count is decremented. 