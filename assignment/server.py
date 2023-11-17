from socket import *
from threading import Thread
import sys, select, time
import json
import re
from datetime import datetime

# {username: (socket, loginTime)}
connectedClients = {}

# {username: timeoutStart}
timeouts = {}

# {groupName: {user: groupStatus}} groupStatus is either "joined" or "invited" 
groupchats = {}

# {username: numAttempsFailed}
failedAttemps = {}

# {username: UdpPortNumber}
userUdpPorts = {}

commandHelp = "\nEnter one of the following commands (/msgto, /activeuser, /creategroup, /joingroup, /groupmsg, /logout):"

def startServer(serverPort, maxFailedAttempts):
    print("Serverport", )
    serverAddress = ("127.0.0.1", serverPort)
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(serverAddress)
    
    with open('userlog.txt', 'w') as f:
        pass  # This will create a new empty userlog.txt file
    with open('messagelog.txt', 'w') as f:
        pass  # This will create a new empty messagelog.txt file
    
    print("Server is running")
    print("Waiting for connection request from clients...")
    
    while True:
        serverSocket.listen()
        clientSocket, clientAddress = serverSocket.accept()
        newClientThread = ClientThread(clientAddress, clientSocket, maxFailedAttempts)
        newClientThread.start()

# Send response back to clientThread

def sendResponseToThread(ClientThread, command, message):
    response = {
        'command': command,
        'message': message,
    }
    ClientThread.clientSocket.send(json.dumps(response).encode('utf-8'))

def sendResponseToSocket(clientSocket, command, message):
    response = {
        'command': command,
        'message': message,
    }
    clientSocket.send(json.dumps(response).encode('utf-8'))

# Logout

def logout(clientThread, connectedClients, message):
    if len(message) > 0:
        sendResponseToThread(clientThread, '', 'Incorrect usage: /logout' + commandHelp)
        return
    
    if clientThread.clientUsername in connectedClients:
        connectedClients.pop(clientThread.clientUsername) 
    if clientThread.clientUsername in userUdpPorts:
        userUdpPorts.pop(clientThread.clientUsername) 
    sendResponseToThread(clientThread, '/logout', 'Logging out of TESSENGER. See you next time!')
    removeUserFromLogs(clientThread.clientUsername)
    time.sleep(0.5)
    print(f"{clientThread.clientUsername} logout")
    clientThread.clientAuthenticated = False
    clientThread.clientUsername = None
    return

def removeUserFromLogs(username):
    with open('userlog.txt', 'r') as f:
        lines = f.readlines()
        
    for idx, line in enumerate(lines):
        if f"; {username};" in line:
            break
    else:
        return  
    
    del lines[idx]
    
    for i in range(idx, len(lines)):
        parts = lines[i].split('; ', 1)
        parts[0] = str(i + 1)
        lines[i] = '; '.join(parts)
        
    with open('userlog.txt', 'w') as f:
        f.writelines(lines)          
        
# Authentication

# Checks if the username and password are in credentials.txt
def authenticateUser(username, password):
    with open("credentials.txt", "r") as f:
        for line in f:
            u, p = line.strip().split()
            if u == username and p == password:
                return True
    return False

def isUserTimedOut(username):
    if username in timeouts.keys():
        timeElapsed = datetime.now() - timeouts[username]
        if timeElapsed.seconds > 10:
            timeouts.pop(username)
            return False
        return True
    else:
        return False

def processLogin(clientThread, message):
    username, password, udpPort = message.split()

    global failedAttemps
    currentFailedAttemps = failedAttemps.get(username, 0)
    
    # Timeout after x failed attempts
    print(f"logging in:\nusername: {username}\npassword: {password}")
    if isUserTimedOut(username):
        sendResponseToThread(clientThread, '/timeout', f"This user is currently timed out, please wait until {timeouts[username]} before trying again")
        
    if currentFailedAttemps + 1 >= clientThread.maxFailedAttempts:
        timeouts[username] = datetime.now()
        sendResponseToThread(clientThread, '/timeout', 'Entered password wrong too many times, please wait 10 seconds before trying again')
        failedAttemps[username] = 0
    elif authenticateUser(username, password): 
        clientThread.clientAuthenticated = True
        clientThread.clientUsername = username
        userUdpPorts[username] = udpPort
        failedAttemps[username] = 0
        
        loginTime = datetime.now().strftime('%d %b %Y %H:%M:%S')
        connectedClients[clientThread.clientUsername] = (clientThread.clientSocket, loginTime)
        
        addToUserlog(clientThread, loginTime)
        sendResponseToThread(clientThread, '/login', 'Authentication successful' + commandHelp)
    else:
        sendResponseToThread(clientThread, '/login', 'Invalid password. Please try again')
        failedAttemps[username] = currentFailedAttemps + 1
    return

def addToUserlog(clientThread, loginTime):
    global userUdpPorts
    ip, _ = clientThread.clientSocket.getpeername()
    with open('userlog.txt', 'a') as f:
        f.write(f"{len(connectedClients)}; {loginTime}; {clientThread.clientUsername}; {ip}; {userUdpPorts[clientThread.clientUsername]}\n")
    return
    
# Group chat services
def createGroup(clientThread, message):
    parts = message.split(' ', 1)
    if len(parts) < 2:
        sendResponseToThread(clientThread, '', 'Incorrect usage: /creategroup groupname USERS' + commandHelp)
        return
    
    groupName, users = parts
        
    clientMessage = ''
    if not re.match(r'^[a-zA-Z0-9]+$', groupName):
        clientMessage = "Invalid group name"
    elif groupName in groupchats.keys():
        clientMessage = f"Group chat {groupName} already exists"
    elif clientThread.clientUsername in users:
        clientMessage = f"You can not invite yourself to a group, try again"
    else:
        chatMembers = {}
        
        # Add owner
        chatMembers[clientThread.clientUsername] = "joined"
        # Invite initial users
        users = users.split(' ')
        for user in users:
            chatMembers[user] = "invited"
            
        groupchats[groupName] = chatMembers
        clientMessage = f"Group chat rom has been created, room name: {groupName}, users in this room: {', '.join(users)}"
        with open(f"{groupName}_messagelog.txt", 'w'):
            pass 
        
    sendResponseToThread(clientThread, '/creategroup', clientMessage + commandHelp)
    return
    
# Join a group chat
def joinGroup(clientThread, groupName):
    if len(groupName.split(' ')) != 1 or groupName == '':
        sendResponseToThread(clientThread, '', 'Incorrect usage: /joingroup groupname' + commandHelp)
        return
    
    global groupchats
    clientMessage = ''
    if groupName not in groupchats.keys():
        clientMessage = "this group chat does not exist"
    elif clientThread.clientUsername not in groupchats[groupName].keys():
        clientMessage = "You have not been invited to this group chat"
    elif groupchats[groupName][clientThread.clientUsername] == 'joined':
        clientMessage = "You have already joined this groupchat"
    else:
        groupchats[groupName][clientThread.clientUsername] = 'joined'
        clientMessage = f"You have joined {groupName} successfully"
    sendResponseToThread(clientThread, '/joingroup', clientMessage + commandHelp)

def groupMsg(clientThread, params):
    if len(params.split(' ')) < 2:
        sendResponseToThread(clientThread, '', 'Incorrect usage: /groupmsg groupname MESSAGE_CONTENT' + commandHelp)
        return
    
    groupName, message = params.split(' ', 1)
        
    clientMessage = ''
    if groupName not in groupchats.keys():
        clientMessage = "This group chat does not exist"
    elif clientThread.clientUsername not in groupchats[groupName].keys():
        clientMessage = "You are not in this group chat"
    elif groupchats[groupName][clientThread.clientUsername] == 'invited':
        clientMessage = "You need to accept the invite before sending a group message"
    else:
        timestamp = datetime.now().strftime("%d %b %Y %H:%M:%S")
        for username, status in groupchats[groupName].items():
            if username != clientThread.clientUsername and status == 'joined' and username in connectedClients.keys():
                (userSocket, timejoined) = connectedClients[username]
                sendResponseToSocket(userSocket, '/groupmsg', f"{timestamp}, {groupName}, {clientThread.clientUsername}: {message}" + commandHelp)  
        logGroupMessage(clientThread.clientUsername, message, groupName, timestamp)
        clientMessage = "Message has been sent!"
    sendResponseToThread(clientThread, '/groupmsg', clientMessage + commandHelp)
    
def logGroupMessage(username, message, groupname, timestamp):
    sequenceNumber = 0
    filename = f"{groupname}_messagelog.txt"
    num = 1
    with open(filename, 'r') as f:
        for num, _ in enumerate(f, 2):
            pass
        sequenceNumber = num
    
    with open(filename, 'a') as f:
        f.write(f"{sequenceNumber}; {timestamp}; {username}; {message}\n")

# Active users 
def getActiveUsers(clientThread, message):

    if len(message) > 0:
        sendResponseToThread(clientThread, '', 'Incorrect usage: /activeuser' + commandHelp)
        return

    activeUsers = connectedClients.copy()
    # remove current user form the copied version of connectedClients
    del activeUsers[clientThread.clientUsername]
    message = "\n"
    
    # 0 users online
    if len(activeUsers) == 0:
        message += "No other active user"
    else:
        global userUdpPorts
        for username, (socket, loginTime) in activeUsers.items():
            ip, _ = socket.getpeername()
            message += f"{username}; {ip}; {userUdpPorts[username]}; active since {str(loginTime)}\n"

    sendResponseToThread(clientThread, '/activeuser', message + commandHelp)
    return

# Msgto command functions

def msgto(clientThread, command, connectedClients): 
    timestamp = datetime.now().strftime("%d %b %Y %H:%M:%S")
    
    if len(command.split(' ')) < 2:
        sendResponseToThread(clientThread, '', 'Incorrect usage: /msgto USERNAME MESSAGE_CONTENT' + commandHelp)
        return
        
    # Only split twice once message can be multiple words
    receiver, message = command.split(' ', 1) 
    
    if receiver in connectedClients:
        (receiverSocket, _) = connectedClients[receiver]
        try:
            sendResponseToSocket(receiverSocket, '', f"[{timestamp}], {clientThread.clientUsername}: {message}" + commandHelp)
            logMessage(receiver, message, timestamp)
        except Exception as e:
            print(f"Error sending message: {e}")   

    sendResponseToThread(clientThread, '/msgto', 'Message has been sent' + commandHelp)
    return

def logMessage(username, message, timestamp):
    sequenceNumber = 0
    count = 1
    with open('messagelog.txt', 'r') as f:
        for count, _ in enumerate(f, 2):
            pass
        sequenceNumber = count
    with open('messagelog.txt', 'a') as f:
        f.write(f"{sequenceNumber}; {timestamp}; {username}; {message}\n")

class ClientThread(Thread):
    def __init__(self, clientAddress, clientSocket, maxFailedAttempts):
        Thread.__init__(self)
        self.clientAddress = clientAddress
        self.clientSocket = clientSocket
        self.clientAuthenticated = False
        self.maxFailedAttempts = maxFailedAttempts
        self.clientUsername = None
        self.closeThread = False

    def run(self):
        global connectedClients
        try:
            while not self.closeThread:
                data = self.clientSocket.recv(1024)
                dict = json.loads(data.decode('utf-8'))

                command = dict['command']
                message = dict['message']
                
                if command == '/login':
                    # Adding client socket to connectedClients
                    processLogin(self, message)    
                elif command == '/msgto':
                    msgto(self, message, connectedClients)
                elif command == '/logout':
                    logout(self, connectedClients, message)
                elif command == '/activeuser':
                    getActiveUsers(self, message)
                elif command == '/creategroup':
                    createGroup(self, message)
                elif command == '/joingroup':
                    joinGroup(self, message)
                elif command == '/groupmsg':
                    groupMsg(self, message)
                else:
                    sendResponseToThread(self, '', 'Invalid command' + commandHelp)
        finally:
            self.clientSocket.close()

if __name__ == '__main__':
    try:
        serverPort = int(sys.argv[1])
        maxFailedAttempts = int(sys.argv[2])
        if maxFailedAttempts < 1 or maxFailedAttempts > 5:
            print("Invalid number of allowed failed consecutive attempts. The valid value of the argument is an integer between 1 and 5.")
            sys.exit(1)
    except ValueError:
        print("Invalid argument types. Both arguments should be integers.")
        sys.exit(1)

    startServer(serverPort, maxFailedAttempts)
