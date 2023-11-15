from socket import *
import sys
from threading import Thread

serverHost = sys.argv[1]
serverPort = int(sys.argv[2])
clientUdpPort = sys.argv[3]
serverAddress = (serverHost, serverPort)

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect(serverAddress)

def listenForMessages(): 
    while True:
        try:
            message = clientSocket.recv(1024).decode()
            if message:
                if message == 'Later gator!':
                    clientSocket.close()
                    break
                print(message)
                print("""\n\nEnter one of the following commands (/msgto, /activeuser, /creategroup, /joingroup, /groupmsg, /p2pvideo ,/logout):""")
        except OSError:
            break
        except Exception as e:
            print(f"error: {e}")
            break
# Creating a thread for when clients can listen to messages
# Used thread to avoid clashes between sending and receiving, client can now do both.
receiverThread = Thread(target=listenForMessages, daemon=True)
receiverThread.start()


def authenticate():
    while True:
        username = input("Enter your username: ")
        password = input("Enter your password: ")
        clientSocket.sendall(f"/login {username} {password}".encode())
        auth_status = clientSocket.recv(1024).decode()
        if auth_status == "Authentication successful":
            break
        print(auth_status)

authenticate()

try:
    while True:
        message = input("""Enter one of the following commands (/msgto, /activeuser, /creategroup, /joingroup, /groupmsg, /p2pvideo ,/logout):\n""")
        if message == '/logout':
            exit;
        clientSocket.sendall(message.encode())
finally:
    clientSocket.close()

