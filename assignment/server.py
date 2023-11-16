from socket import *
from threading import Thread
import sys, select, time
import json
from datetime import datetime

# {username: (socket, loginTime)}
connectedClients = {}

# {username: timeoutStart}
timeouts = {}

def startServer(serverPort, maxFailedAttempts):
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

    if command != '/logout' and (command == '/login' and message == 'Authentication successful'):
        response['message'] += "\nEnter one of the following commands (/msgto, /activeuser, /creategroup, /joingroup, /groupmsg, /p2pvideo ,/logout):\n"
    
    print("Sending response to client", message)
    ClientThread.clientSocket.send(json.dumps(response).encode('utf-8'))

def sendResponseToSocket(clientSocket, command, message):
    response = {
        'command': command,
        'message': message,
    }
    print("Sending response to client")
    clientSocket.send(json.dumps(response).encode('utf-8'))
# Logout

def logout(clientThread, connectedClients):
    if clientThread.clientUsername in connectedClients:
        connectedClients.pop(clientThread.clientUsername)
    sendResponseToThread(clientThread, '/logout', 'Logging out of TESSENGER. See you next time!')
    removeUserFromLogs(clientThread.clientUsername)
    clientThread.clientSocket.close()

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

def processLogin(clientThread, username, password):
    # Timeout after x failed attempts
    if isUserTimedOut(username):
        sendResponseToThread(clientThread, '/timeout', f"This user is currently timed out, please wait until {timeouts[username]} before trying again")
        
    if clientThread.failedAttempts + 1 >= clientThread.maxFailedAttempts:
        timeouts[username] = datetime.now().strftime('%d %b %Y %H:%M:%S')
        sendResponseToThread(clientThread, '/timeout', 'Entered password wrong too many times, please wait 10 seconds before trying again')
        clientThread.failedAttempts = 0
    elif authenticateUser(username, password): 
        clientThread.clientAuthenticated = True
        clientThread.clientUsername = username
        clientThread.failedAttempts = 0
        
        loginTime = datetime.now().strftime('%d %b %Y %H:%M:%S')
        connectedClients[clientThread.clientUsername] = (clientThread.clientSocket, loginTime)
        
        addToUserlog(clientThread, loginTime)
        sendResponseToThread(clientThread, '/login', 'Authentication successful')
    else:
        sendResponseToThread(clientThread, '/login', 'Invalid password. Please try again')
        clientThread.failedAttempts += 1
    return

def addToUserlog(clientThread, loginTime):
    ip, port = clientThread.clientSocket.getpeername()
    with open('userlog.txt', 'a') as f:
        f.write(f"{len(connectedClients)}; {loginTime}; {clientThread.clientUsername}; {ip}; {port}\n")
    return
        
# Active users 

def getActiveUsers(clientThread):
    # print(f"Current active users:\n{connectedClients}\n")
    activeUsers = connectedClients.copy()
    # remove current user form the copied version of connectedClients
    del activeUsers[clientThread.clientUsername]
    message = "\n"
    
    # 0 users online
    if len(activeUsers) == 0:
        message += "No other active user"
    else:
        for username, (socket, loginTime) in activeUsers.items():
            ip, port = socket.getpeername()
            message += f"{username}; {ip}; {port}; active since {str(loginTime)}\n"

    sendResponseToThread(clientThread, '/activeuser', message)
    return

# Msgto command functions

def debugPrint(clientThread, command, connectedClients):
    print("Message Commands Debug")
    print(f"|    sent by: {clientThread.clientUsername}")
    print(f"|    contents: {command}")
    print(f"|    connected clients: {connectedClients}")
    return

def msgto(clientThread, command, connectedClients): 
    timestamp = datetime.now().strftime("%d %b %Y %H:%M:%S")
    
    # debugPrint(clientThread, command, connectedClients)

    if len(command) < 2:
        sendResponseToThread(clientThread, '/msgto', 'Incorrect usage: /msgto USERNAME MESSAGE_CONTENT')
        
    # Only split twice once message can be multiple words
    receiver, message = command.split(' ', 1) 

    # print(f"Trying to send message:\nsender: {clientThread.clientUsername}\nreceiver: {receiver}\nmessage: {message}\n")
    
    if receiver in connectedClients:
        (receiverSocket, _) = connectedClients[receiver]
        try:
            sendResponseToSocket(receiverSocket, '', f"[{timestamp}] From {clientThread.clientUsername}: {message}")
            logMessage(receiver, message, timestamp)
        except Exception as e:
            print(f"Error sending message: {e}")   

    sendResponseToThread(clientThread, '/msgto', 'Message has been sent')
    return

def logMessage(username, message, timestamp):
    with open('messagelog.txt', 'a') as f:
        f.seek(0)
        messageNumber = sum(1 for _ in f) + 1
        f.write(f"{messageNumber}; {timestamp}; {username}; {message}\n")


class ClientThread(Thread):
    def __init__(self, clientAddress, clientSocket, maxFailedAttempts):
        Thread.__init__(self)
        self.clientAddress = clientAddress
        self.clientSocket = clientSocket
        self.clientAuthenticated = False
        self.failedAttempts = 0
        self.maxFailedAttempts = maxFailedAttempts
        self.clientUsername = None

    def run(self):
        global connectedClients
        try:
            while True:
                data = self.clientSocket.recv(1024)
                dict = json.loads(data.decode('utf-8'))
                print('dict:', dict)

                command = dict['command']
                message = dict['message']
                
                if command == '/login':
                    username, password = message.split()
                    # Adding client socket to connectedClients
                    processLogin(self, username, password)    
                elif command == '/msgto':
                    msgto(self, message, connectedClients)
                elif command == '/logout':
                    logout(self, connectedClients)
                    break
                elif command == '/activeuser':
                    getActiveUsers(self)
                else:
                    sendResponseToThread(self, '', 'Invalid command')
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
