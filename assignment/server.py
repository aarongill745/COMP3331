from socket import *
from threading import Thread
import sys, select, time


def logLogin(username):
    with open('userlog.txt', 'w') as f:
        f.write()


# Function to authenticate user
def authenticate_user(username, password):
    # Finds username and password in credentials.txt
    with open("credentials.txt", "r") as f:
        for line in f:
            u, p = line.strip().split()
            if u == username and p == password:
                return True
    return False

try:
    serverPort = int(sys.argv[1])
    max_failed_attempts = int(sys.argv[2])
    if max_failed_attempts < 1 or max_failed_attempts > 5:
        print("Invalid number of allowed failed consecutive attempts. The valid value of the argument is an integer between 1 and 5.")
        sys.exit(1)
except ValueError:
    print("Invalid argument types. Both arguments should be integers.")
    sys.exit(1)

serverAddress = ("127.0.0.1", serverPort)
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(serverAddress)

failed_attempts = 0

class ClientThread(Thread):
    def __init__(self, clientAddress, clientSocket):
        Thread.__init__(self)
        self.clientAddress = clientAddress
        self.clientSocket = clientSocket
        self.clientAuthenticated = False

    def run(self):
        global failed_attempts
        while True:
            data = self.clientSocket.recv(1024)
            message = data.decode()

            if message == 'login':
                self.process_login()
            elif message == 'download':
                self.process_download()

            if failed_attempts >= max_failed_attempts:
                time.sleep(10)
                failed_attempts = 0
                self.process_login()

    def process_login(self):
        global failed_attempts
        self.clientSocket.send('user credentials request'.encode())
        credentials = self.clientSocket.recv(1024).decode().split()
        if authenticate_user(credentials[0], credentials[1]):
            self.clientAuthenticated = True
            self.clientSocket.send("Authentication successful".encode())
            client_udp_port = self.clientSocket.recv(1024).decode()  # Receive UDP port
            timestamp = time.strftime("%d %b %Y %H:%M:%S", time.gmtime())
            with open("userlog.txt", "a") as f:
                f.write(f"1; {timestamp}; {credentials[0]}; {self.clientAddress[0]}; {client_udp_port}\n")
            failed_attempts = 0
        else:
            self.clientSocket.send("Invalid Password. Please try again".encode())
            failed_attempts += 1
            self.process_login()

    def process_download(self):
        if self.clientAuthenticated:
            self.clientSocket.send('download filename'.encode())
        else:
            self.clientSocket.send("Please login first".encode())

print("Server is running")
print("Waiting for connection request from clients...")

while True:
    serverSocket.listen()
    clientSocket, clientAddress = serverSocket.accept()
    clientThread = ClientThread(clientAddress, clientSocket)
    clientThread.start()
