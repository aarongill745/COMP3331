from socket import *
from threading import Thread
import sys, select

def authenticate_user(username, password):
    with open("credentials.txt", "r") as f:
        for line in f:
            u, p = line.strip().split()
            if u == username and p == password:
                return True
    return False

serverPort = int(sys.argv[1])
serverAddress = ("127.0.0.1", serverPort)
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(serverAddress)

class ClientThread(Thread):
    def __init__(self, clientAddress, clientSocket):
        Thread.__init__(self)
        self.clientAddress = clientAddress
        self.clientSocket = clientSocket
        self.clientAlive = True
        self.clientAuthenticated = False

        print("New connection created for: ", clientAddress)
        self.clientAlive = True

    def run(self):
        while self.clientAlive:
            data = self.clientSocket.recv(1024)
            message = data.decode()
            if message == '':
                self.clientAlive = False
                print("User disconnected - ", self.clientAddress)
                break

            if message == 'login':
                self.process_login()
            elif message == 'download':
                self.process_download()
            else:
                message = 'Cannot understand this message'
                self.clientSocket.send(message.encode())
    
    def process_login(self):
        message = 'user credentials request'
        self.clientSocket.send(message.encode())
        credentials = self.clientSocket.recv(1024).decode().split()
        if authenticate_user(credentials[0], credentials[1]):
            self.clientAuthenticated = True
            self.clientSocket.send("Authentication successful".encode())
        else:
            self.clientSocket.send("Authentication failed".encode())

    def process_download(self):
        if self.clientAuthenticated:
            message = 'download filename'
            self.clientSocket.send(message.encode())
        else:
            self.clientSocket.send("Please login first".encode())

print("Server is running")
print("Waiting for connection request from clients...")

while True:
    serverSocket.listen()
    clientSocket, clientAddress = serverSocket.accept()
    clientThread = ClientThread(clientAddress, clientSocket)
    clientThread.start()
