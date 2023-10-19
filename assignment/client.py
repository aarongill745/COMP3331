from socket import *
import sys

serverHost = sys.argv[1]
serverPort = int(sys.argv[2])
serverAddress = (serverHost, serverPort)
clientSocket = socket(AF_INET, SOCK_STREAM)

clientSocket.connect(serverAddress)

def messageReceived():
    username = input("Enter your username: ")
    password = input("Enter your password: ")
    clientSocket.sendall(f"{username} {password}".encode())
    auth_status = clientSocket.recv(1024).decode()
    print(f"[recv] {auth_status}")



while True:
    message = input("Please type any message you want to send to server:\n")
    clientSocket.sendall(message.encode())
    data = clientSocket.recv(1024)
    receivedMessage = data.decode()

    if receivedMessage == "user credentials request":
        messageReceived()

    elif receivedMessage == "download filename":
        filename = input("Enter the filename to download: ")
        print(f"Downloading {filename}...")

    elif receivedMessage == "Please login first":
        print("[recv] You need to login first.")
        
    else:
        print("[recv] Message makes no sense")

    ans = input('Do you want to continue(y/n): ')
    if ans == 'n':
        break

clientSocket.close()
