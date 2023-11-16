from socket import *
import sys
import json
import time
from threading import Thread

serverHost = sys.argv[1]
serverPort = int(sys.argv[2])
serverAddress = (serverHost, serverPort)

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect(serverAddress)

authenticated = False
while not authenticated:
    username = input("Enter your username: ")
    password = input("Enter your password: ")
    
    if not username:
        username = ''
    if not password:
        password = ''
    
    payload = {
        'command': '/login',
        'message': f"{username} {password}"
    }
    
    clientSocket.sendall(json.dumps(payload).encode('utf-8'))
    
    response = clientSocket.recv(1024).decode('utf-8')
    dict_response = json.loads(response) 
    
    if "Authentication successful" in dict_response['message']:
        authenticated = True
        
    print(dict_response['message'])

def listenForMessages(): 
    while True:
        try:
            response = clientSocket.recv(1024).decode('utf-8')
            if not response:
                break
            dict_response = json.loads(response)
            if dict_response['command'] == '/logout':
                print("Logged out.")
                clientSocket.close()
                break
            print(dict_response['message'])
        except OSError:
            break
        except Exception as e:
            print(f"error: {e}")
            break
    sys.exit()

# Start listening for messages in a separate thread
receiverThread = Thread(target=listenForMessages, daemon=True)
receiverThread.start()

try:
    while True:
        message = input()
        if not message:
            continue
        command, *args = message.split()
        
        if not args:
            args = ''
            
        payload = {
            'command': command,
            'message': ' '.join(args)
        }
        
        clientSocket.sendall(json.dumps(payload).encode('utf-8'))
finally:
    clientSocket.close()
