from datetime import datetime

def debugPrint(clientThread, command, connectedClients):
    print("Message Commands Debug")
    print(f"|    sent by: {clientThread.clientUsername}")
    print(f"|    contents: {command}")
    print(f"|    connected clients: {connectedClients}")
    return

def sendPrivateMessage(clientThread, command, connectedClients): 
    timestamp = datetime.now().strftime("%d %b %Y %H:%M:%S")
    
    # debugPrint(clientThread, command, connectedClients)

    # Only split twice since message can be multiple words
    _, receiver, message = command.split(' ', 2) 
    
    if receiver in connectedClients:
        receiverSocket = connectedClients[receiver]
        try:
            receiverSocket.send(f"[{timestamp}] From {clientThread.clientUsername}: {message}".encode())
            logMessage(receiver, message, timestamp)
        except Exception as e:
            print(f"Error sending message: {e}")   
    clientThread.clientSocket.send(f"Message has been sent to {receiver}".encode())
    return

def logMessage(username, message, timestamp):
    with open('messagelog.txt', 'a') as f:
        f.seek(0)
        messageNumber = sum(1 for _ in f) + 1
        f.write(f"{messageNumber}; {timestamp}; {username}; {message}\n")
        
        