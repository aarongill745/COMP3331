from socket import *
from threading import Thread
import sys, select, time
import authentication 
import messageCommands
import logout

connectedClients = {}
def startServer(serverPort, maxFailedAttempts):
    serverAddress = ("127.0.0.1", serverPort)
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(serverAddress)
    open('userlog.txt', 'a')
    open('messagelog.txt', 'a')
    print("Server is running")
    print("Waiting for connection request from clients...")
    
    while True:
        serverSocket.listen()
        clientSocket, clientAddress = serverSocket.accept()
        newClientThread = ClientThread(clientAddress, clientSocket, maxFailedAttempts)
        newClientThread.start()


def getActiveUsers(clientThread):
    print(f"Current active users:\n{connectedClients}\n")
    activeUsers = connectedClients.copy()
    del activeUsers[clientThread.clientUsername]
    if len(activeUsers) == 0:
        clientThread.clientSocket.send("There are no active users at the moment")
        return
    else:
        for username, _ in activeUsers.items():
            ip, port = clientThread.clientSocket.getpeername()
            clientThread.clientSocket.send(f"{username}; {ip}; {port}; active since {time}")
        print("What does this print:", clientThread.clientSocket.getpeername())        
    return

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
                message = data.decode().strip()
                command = message.split()[0]
                print("Command:", command)
                if command == '/login':
                    username, password = message.split()[1], message.split()[2]
                    # Adding client socket to connectedClients
                    if authentication.processLogin(self, username, password):
                        connectedClients[self.clientUsername] = self.clientSocket
                elif command == '/msgto':
                    messageCommands.sendPrivateMessage(self, message, connectedClients)
                elif command == '/logout':
                    logout.logout(self , connectedClients)
                    break
                elif command == '/activeuser':
                    getActiveUsers(self)
                else:
                    self.clientSocket.send("Invalid command".encode())
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
